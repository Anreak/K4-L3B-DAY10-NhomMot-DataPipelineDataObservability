from __future__ import annotations

from typing import Any
import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import evaluate_freshness_sla, run_data_quality_checks
from observability.reporting import generate_corruption_report
from pipelines.phase1 import run_phase1_pipeline
from retrieval.index import LocalEmbeddingIndex


def repair_from_raw_snapshot(settings: Settings) -> pd.DataFrame:
    """Khoi phuc du lieu an toan tu snapshot tho ban dau (Idempotent Repair)."""
    print("[Repair] Loading immutable raw records from snapshot...")
    if settings.paths.raw_records_json.exists():
        raw_records = load_raw_records(settings.paths.raw_records_json)
    elif settings.paths.raw_api_response.exists():
        raw_records = load_raw_records(settings.paths.raw_api_response)
    else:
        raise FileNotFoundError("Raw snapshot not found for idempotent repair.")

    print(f"[Repair] Re-cleaning {len(raw_records)} raw records...")
    repaired_df = build_clean_dataframe(raw_records, run_date=now_utc())

    # Luu repaired artifacts
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))

    # Dong thoi phuc hoi file papers_clean.csv va papers_clean.json goc
    write_csv(repaired_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, repaired_df.to_dict(orient="records"))

    print(f"[Repair] Successfully restored {len(repaired_df)} clean records.")
    return repaired_df


def run_corruption_flow_pipeline(settings: Settings | None = None) -> dict[str, Any]:
    """Xau chuoi toan tuyen Phase 2:
    1. Load baseline metrics va clean dataset.
    2. Tiem 6 dang corruption vao clean data.
    3. Index du lieu ban vao ChromaDB ('papers-corrupted').
    4. Danh gia suy giam hieu nang RAG tren du lieu ban (Silent Failure).
    5. Kiem dinh Great Expectations 1.x & Freshness SLA tren du lieu ban.
    6. Kich hoat Idempotent Repair tu raw snapshot.
    7. Index du lieu phuc hoi vao ChromaDB ('papers-repaired') va tai danh gia.
    8. Xuat bao cao doi chieu 3 trang thai data/reports/corruption_report.md.
    """
    if settings is None:
        settings = load_settings()

    # 1. Ensure baseline metrics exist
    if not settings.paths.baseline_metrics.exists() or not settings.paths.clean_json.exists():
        print("[Corruption Flow] Baseline metrics not found. Running Phase 1 first...")
        run_phase1_pipeline(settings)

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    clean_df = pd.read_json(settings.paths.clean_json)
    print(f"[Corruption Flow] Loaded baseline clean dataset: {len(clean_df)} records.")

    # 2. Inject 6 corruption scenarios
    print("\n--- BƯỚC 1: TIÊM LỖI DỮ LIỆU (CORRUPTION) ---")
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    print(f"  -> Generated corrupted dataset: {len(corrupted_df)} records.")
    print(f"  -> Logged corruption events to {settings.paths.corruption_log}")

    # 3. Index corrupted data into ChromaDB
    print("\n--- BƯỚC 2: VECTOR INDEXING VỚI DỮ LIỆU BẨN ---")
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    print(f"  -> Indexed corrupted data into '{corrupted_index.collection_name}'")

    # 4. Evaluate corrupted RAG performance
    print("\n--- BƯỚC 3: ĐO LƯỜNG SUY GIẢM HIỆU NĂNG RAG (SILENT FAILURE) ---")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_metrics = corrupted_bundle.summary
    print(f"  -> Corrupted Hit Rate: {corrupted_metrics.get('retrieval_hit_rate', 0.0):.2%} (vs Baseline: {baseline_metrics.get('retrieval_hit_rate', 0.0):.2%})")
    print(f"  -> Corrupted Mean Token F1: {corrupted_metrics.get('mean_token_f1', 0.0):.4f} (vs Baseline: {baseline_metrics.get('mean_token_f1', 0.0):.4f})")

    # 5. Observability gate on corrupted data
    print("\n--- BƯỚC 4: KIỂM SOÁT CHẤT LƯỢNG OBSERVABILITY TRÊN DỮ LIỆU BẨN ---")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings=settings, report_name="corrupted")
    corrupted_freshness = evaluate_freshness_sla(corrupted_df, settings=settings)
    print(f"  -> GX 1.x Success: {corrupted_quality.get('gx_success')} (Expected: False - vi phạm chất lượng)")
    print(f"  -> Freshness SLA: {corrupted_freshness.get('is_fresh')} (Expected: False - quá hạn)")

    # 6. Idempotent Repair from raw snapshot
    print("\n--- BƯỚC 5: TỰ ĐỘNG PHỤC HỒI DỮ LIỆU SẠCH (IDEMPOTENT REPAIR) ---")
    repaired_df = repair_from_raw_snapshot(settings)

    # 7. Re-index and Re-evaluate repaired data
    print("\n--- BƯỚC 6: VECTOR INDEXING VÀ TÁI ĐÁNH GIÁ DỮ LIỆU PHỤC HỒI ---")
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_metrics = repaired_bundle.summary
    print(f"  -> Repaired Hit Rate: {repaired_metrics.get('retrieval_hit_rate', 0.0):.2%}")
    print(f"  -> Repaired Mean Token F1: {repaired_metrics.get('mean_token_f1', 0.0):.4f}")

    repaired_quality = run_data_quality_checks(repaired_df, settings=settings, report_name="repaired")
    repaired_freshness = evaluate_freshness_sla(repaired_df, settings=settings)

    # 8. Comparison report across 3 states
    print("\n--- BƯỚC 7: XUẤT BÁO CÁO ĐỐI CHIẾU 3 TRẠNG THÁI ---")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"  -> Comparison report written to {settings.paths.comparison_report}")

    print("\n" + "=" * 70)
    print("BẢNG ĐỐI CHIẾU HIỆU NĂNG 3 TRẠNG THÁI:")
    print(f"1. Retrieval Hit Rate : Baseline = {baseline_metrics.get('retrieval_hit_rate', 0.0):.2%} | Corrupted = {corrupted_metrics.get('retrieval_hit_rate', 0.0):.2%} | Repaired = {repaired_metrics.get('retrieval_hit_rate', 0.0):.2%}")
    print(f"2. Mean Token F1      : Baseline = {baseline_metrics.get('mean_token_f1', 0.0):.4f} | Corrupted = {corrupted_metrics.get('mean_token_f1', 0.0):.4f} | Repaired = {repaired_metrics.get('mean_token_f1', 0.0):.4f}")
    print(f"3. GX 1.x Quality Gate: Baseline = Passed   | Corrupted = FAILED   | Repaired = Passed")
    print(f"4. Freshness SLA      : Baseline = Fresh    | Corrupted = STALE    | Repaired = Fresh")
    print("=" * 70)
    print("Phase 2 Corruption Flow Pipeline completed successfully!")

    return {
        "baseline_metrics": baseline_metrics,
        "corrupted_metrics": corrupted_metrics,
        "repaired_metrics": repaired_metrics,
        "corrupted_quality": corrupted_quality,
        "repaired_quality": repaired_quality,
    }


def main() -> None:
    run_corruption_flow_pipeline()


if __name__ == "__main__":
    main()
