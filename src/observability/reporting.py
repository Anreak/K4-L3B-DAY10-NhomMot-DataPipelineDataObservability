from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import now_utc, write_text


def _expectations_table(expectations: list[dict[str, Any]]) -> str:
    lines = ["| Expectation | Success |", "| --- | --- |"]
    for item in expectations:
        status = "PASS" if item["success"] else "FAIL"
        lines.append(f"| `{item['expectation_type']}` | {status} |")
    return "\n".join(lines)


def generate_phase1_report(
    report_path: Path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Xuat bao cao markdown cho Baseline Pipeline (Phase 1): source, metrics, quality gate, freshness."""
    gate_status = "PASS" if quality.get("success") else "FAIL"
    ragas = metrics.get("ragas", {})
    ragas_line = (
        "Ragas: bỏ qua (đặt `RUN_RAGAS=1` để bật)."
        if "skipped" in ragas
        else "\n".join(f"- {key}: {value}" for key, value in ragas.items())
    )

    report = f"""# Phase 1 Baseline Report

_Sinh lúc: {now_utc().isoformat()}_

## 1. Nguồn Dữ Liệu

- Source API: {source_summary.get('source_api')}
- Tổng số bản ghi thu thập: {source_summary.get('total_records')}
- Số dòng sau khi làm sạch: {source_summary.get('clean_rows')}

## 2. Baseline RAG Evaluation

| Metric | Giá trị |
| --- | --- |
| Samples | {metrics.get('samples')} |
| Retrieval Hit Rate | {metrics.get('retrieval_hit_rate', 0):.2%} |
| Mean Token F1 | {metrics.get('mean_token_f1', 0):.4f} |
| Judge Accuracy | {metrics.get('judge_accuracy', 0):.2%} |
| Mean Judge Score | {metrics.get('mean_judge_score', 0):.2f} / 5 |

{ragas_line}

## 3. Data Quality Gate (Great Expectations 1.x)

- Trạng thái chốt kiểm soát: **{gate_status}**
- GX Expectations Success: {quality.get('gx_success')}
- Số dòng kiểm tra: {quality.get('row_count')}

{_expectations_table(quality.get('expectations', []))}

## 4. Freshness SLA

- Ngưỡng freshness: {freshness.get('freshness_threshold_days')} ngày
- Bài báo quá hạn: {freshness.get('stale_rows')}/{freshness.get('total_rows')} ({freshness.get('stale_ratio', 0):.1%})
- Kết quả Freshness (is_fresh): {freshness.get('is_fresh')}
"""

    write_text(Path(report_path), report)


def generate_corruption_report(
    report_path: Path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    raise NotImplementedError("Student task: implement corruption comparison report.")
