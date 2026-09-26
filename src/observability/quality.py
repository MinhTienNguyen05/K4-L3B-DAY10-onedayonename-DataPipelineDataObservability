from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import ensure_parent, write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Chạy bộ kiểm thử chất lượng dữ liệu bằng Great Expectations 1.x Ephemeral Context.

    4 Expectations bắt buộc:
    1. ExpectTableRowCountToBeBetween: 5-5000 rows
    2. ExpectColumnValuesToNotBeNull: paper_id, title, text_for_embedding
    3. ExpectColumnValuesToBeUnique: paper_id
    4. ExpectColumnValueLengthsToBeBetween: summary >= 30 chars
    """
    # 1. Khởi tạo Great Expectations 1.x Ephemeral Context
    context = gx.get_context(mode="ephemeral")

    source_name = f"papers_source_{report_name}"
    try:
        data_source = context.data_sources.add_pandas(name=source_name)
    except Exception:
        data_source = context.data_sources.get(source_name)

    asset_name = f"papers_asset_{report_name}"
    try:
        data_asset = data_source.add_dataframe_asset(name=asset_name)
    except Exception:
        data_asset = data_source.get_asset(asset_name)

    batch_def_name = f"papers_batch_{report_name}"
    try:
        batch_def = data_asset.add_batch_definition_whole_dataframe(batch_def_name)
    except Exception:
        batch_def = data_asset.get_batch_definition(batch_def_name)

    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    # 2. Xây dựng ExpectationSuite với 4 Expectations thiết yếu
    suite_name = f"papers_{report_name}_suite"
    try:
        suite = context.suites.add(gx.ExpectationSuite(name=suite_name))
    except Exception:
        try:
            suite = context.suites.get(suite_name)
        except Exception:
            suite = gx.ExpectationSuite(name=suite_name)

    expectations = [
        gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
        gxe.ExpectColumnValuesToNotBeNull(column="paper_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="title"),
        gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
        gxe.ExpectColumnValuesToBeUnique(column="paper_id"),
        gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
    ]

    for exp in expectations:
        suite.add_expectation(exp)

    # 3. Thực thi kiểm định chất lượng (Validate Batch)
    validation_result = batch.validate(suite)

    # 4. Trích xuất kết quả chi tiết
    results_list: list[dict[str, Any]] = []
    for r in validation_result.results:
        exp_type = getattr(r.expectation_config, "type", str(type(r)))
        exp_kwargs = dict(getattr(r.expectation_config, "kwargs", {}))
        result_payload = dict(getattr(r, "result", {}))
        results_list.append(
            {
                "expectation": exp_type,
                "kwargs": exp_kwargs,
                "success": bool(r.success),
                "result": result_payload,
            }
        )

    evaluated_count = len(validation_result.results)
    successful_count = sum(1 for r in validation_result.results if r.success)
    unsuccessful_count = evaluated_count - successful_count
    overall_success = bool(validation_result.success)

    report_payload: dict[str, Any] = {
        "report_name": report_name,
        "success": overall_success,
        "total_records": len(df),
        "evaluated_expectations": evaluated_count,
        "successful_expectations": successful_count,
        "unsuccessful_expectations": unsuccessful_count,
        "results": results_list,
    }

    # 5. Xác định đường dẫn file lưu báo cáo
    if report_name == "baseline":
        output_path = settings.paths.baseline_quality_report
    elif report_name == "corrupted":
        output_path = settings.paths.corrupted_quality_report
    else:
        output_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"

    write_json(output_path, report_payload)
    return report_payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tổng hợp báo cáo độ tươi mới của dữ liệu (Freshness SLA).

    - Ngưỡng quá hạn (stale): age_days > settings.freshness_threshold_days (180 ngày).
    - SLA fresh: tỷ lệ stale_ratio <= 0.25 (<= 25%).
    """
    total_rows = len(df)
    latest_published = (
        str(df["published"].max())
        if not df.empty and "published" in df.columns and pd.notna(df["published"].max())
        else None
    )
    oldest_published = (
        str(df["published"].min())
        if not df.empty and "published" in df.columns and pd.notna(df["published"].min())
        else None
    )

    if not df.empty and "age_days" in df.columns:
        stale_mask = df["age_days"] > settings.freshness_threshold_days
        stale_rows = int(stale_mask.sum())
        max_age_days = int(df["age_days"].max()) if pd.notna(df["age_days"].max()) else 0
        mean_age_days = float(df["age_days"].mean()) if pd.notna(df["age_days"].mean()) else 0.0
    else:
        stale_rows = 0
        max_age_days = 0
        mean_age_days = 0.0

    stale_ratio = float(stale_rows / total_rows) if total_rows > 0 else 0.0
    is_fresh = bool(stale_ratio <= 0.25)

    payload: dict[str, Any] = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "total_rows": total_rows,
        "stale_rows": stale_rows,
        "stale_ratio": round(stale_ratio, 4),
        "freshness_threshold_days": settings.freshness_threshold_days,
        "sla_stale_limit_ratio": 0.25,
        "is_fresh": is_fresh,
        "max_age_days": max_age_days,
        "mean_age_days": round(mean_age_days, 1),
    }

    target_path = Path(report_path)
    write_json(target_path, payload)
    return payload
