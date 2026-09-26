from __future__ import annotations

from core.config import Settings, load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def run_phase1_pipeline(settings: Settings) -> dict:
    """Chay xau chuoi 6 buoc Baseline Pipeline (Phase 1):

    1. Ingest: thu thap/doc snapshot Crossref.
    2. Clean: chuan hoa thanh dataframe sach + text_for_embedding, luu CSV/JSON.
    3. Index ChromaDB: nap embedding MiniLM vao collection `papers-baseline`.
    4. Sinh Benchmark Test Set (10 cau Ground Truth).
    5. Danh gia Baseline RAG (Retrieval Hit Rate & Token F1).
    6. Great Expectations Quality Gate + Freshness SLA, sau do xuat `phase1_report.md`.
    """
    run_date = now_utc()

    records = fetch_source_records(settings)

    df = build_clean_dataframe(records, run_date)
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))

    index = LocalEmbeddingIndex.build(df, settings)

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(df, settings.paths.eval_testset)

    evaluation = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )

    quality = run_data_quality_checks(df, settings, "baseline")

    source_summary = {
        "source_api": settings.source_api,
        "total_records": len(records),
        "clean_rows": len(df),
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary,
        evaluation.summary,
        quality,
        quality["freshness"],
    )

    return {
        "records": records,
        "clean_df": df,
        "index": index,
        "evaluation": evaluation,
        "quality": quality,
    }


def main() -> None:
    settings = load_settings()
    run_phase1_pipeline(settings)


if __name__ == "__main__":
    main()
