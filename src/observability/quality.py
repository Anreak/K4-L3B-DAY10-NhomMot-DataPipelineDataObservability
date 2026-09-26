from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd

from core.config import Settings

_MIN_ROWS = 5
_MAX_ROWS = 5000
_NOT_NULL_COLUMNS = ("paper_id", "title", "text_for_embedding")
_MIN_SUMMARY_CHARS = 30
_STALE_RATIO_THRESHOLD = 0.25


def _build_expectation_suite() -> gx.ExpectationSuite:
    """4 hang rao kiem dinh bat buoc truoc khi du lieu vao Vector Database."""
    suite = gx.ExpectationSuite(name="papers_quality_suite")
    suite.add_expectation(
        gx.expectations.ExpectTableRowCountToBeBetween(min_value=_MIN_ROWS, max_value=_MAX_ROWS)
    )
    for column in _NOT_NULL_COLUMNS:
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column=column))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(
        gx.expectations.ExpectColumnValueLengthsToBeBetween(
            column="summary", min_value=_MIN_SUMMARY_CHARS
        )
    )
    return suite


def _validate_with_gx(df: pd.DataFrame) -> gx.core.expectation_validation_result.ExpectationSuiteValidationResult:
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})
    return batch.validate(_build_expectation_suite())


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path) -> dict[str, Any]:
    """Tong hop Freshness SLA: canh bao `is_fresh=False` neu >25% bai bao co age_days > nguong."""
    total_rows = len(df)

    if total_rows == 0:
        payload: dict[str, Any] = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "freshness_threshold_days": settings.freshness_threshold_days,
            "is_fresh": True,
        }
    else:
        stale_mask = df["age_days"] > settings.freshness_threshold_days
        stale_rows = int(stale_mask.sum())
        stale_ratio = stale_rows / total_rows

        payload = {
            "latest_published": str(df["published"].max()),
            "oldest_published": str(df["published"].min()),
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "stale_ratio": stale_ratio,
            "freshness_threshold_days": settings.freshness_threshold_days,
            "is_fresh": stale_ratio <= _STALE_RATIO_THRESHOLD,
        }

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def evaluate_freshness_sla(
    df: pd.DataFrame, settings: Settings, report_path: Path | None = None
) -> dict[str, Any]:
    """Danh gia Freshness SLA theo settings."""
    target_path = report_path if report_path is not None else settings.paths.freshness_report
    return build_freshness_report(df, settings, target_path)



def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Thiet lap Observability Gate: 4 Expectations (GX 1.x Ephemeral Context) + Freshness SLA.

    Data chi duoc coi la "sach" (`success=True`) khi vuot qua ca 4 Expectations
    LAN Freshness SLA. Ket qua duoc ghi vao `data/quality/<report_name>_quality_report.json`.
    """
    gx_result = _validate_with_gx(df)
    expectations = [
        {"expectation_type": result.expectation_config.type, "success": result.success}
        for result in gx_result.results
    ]

    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)

    report = {
        "stage": report_name,
        "row_count": len(df),
        "gx_success": gx_result.success,
        "expectations": expectations,
        "freshness": freshness,
        "success": bool(gx_result.success and freshness["is_fresh"]),
    }

    report_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return report
