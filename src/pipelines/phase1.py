from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Build baseline pipeline end-to-end.

    Steps:
    1. Load settings.
    2. Load or fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Create or load evaluation set.
    7. Evaluate.
    8. Run quality checks and freshness report.
    9. Generate markdown report.
    """
    print("=" * 60)
    print("PHASE 1: BASELINE PIPELINE")
    print("=" * 60)

    # 1. Load settings
    settings = load_settings()
    print("\n[1/9] Settings loaded.")

    # 2. Load or fetch raw records
    raw_path = settings.paths.raw_records_json
    if settings.refresh_source or not raw_path.exists():
        print("\n[2/9] Fetching source records from Crossref API...")
        records = fetch_source_records(settings)
        print(f"  Fetched {len(records)} records from Crossref API.")
    else:
        print("\n[2/9] Loading raw records from local cache...")
        records = load_raw_records(raw_path)
        print(f"  Loaded {len(records)} records from cache.")

    # 3. Clean data
    print("\n[3/9] Cleaning data...")
    run_date = now_utc()
    df = build_clean_dataframe(records, run_date)
    print(f"  Cleaned {len(df)} records.")

    # 4. Save clean CSV/JSON
    print("\n[4/9] Saving clean artifacts...")
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))
    print(f"  Saved to {settings.paths.clean_csv} and {settings.paths.clean_json}")

    # 5. Build Chroma index
    print("\n[5/9] Building ChromaDB index...")
    index = LocalEmbeddingIndex.build(df, settings)
    print(f"  Indexed {len(index.documents)} documents in collection '{index.collection_name}'.")

    # 6. Create or load evaluation set
    print("\n[6/9] Preparing evaluation test set...")
    test_set_path = settings.paths.eval_testset
    if settings.refresh_test_set or not test_set_path.exists():
        test_set = build_test_set(df, test_set_path)
        print(f"  Generated {len(test_set)} test questions.")
    else:
        test_set = read_json(test_set_path)
        print(f"  Loaded {len(test_set)} test questions from cache.")

    # 7. Evaluate
    print("\n[7/9] Running evaluation...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=test_set_path,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print(f"  Hit Rate: {bundle.summary['retrieval_hit_rate']:.2%}")
    print(f"  Mean Token F1: {bundle.summary['mean_token_f1']:.4f}")
    print(f"  Judge Accuracy: {bundle.summary['judge_accuracy']:.2%}")
    print(f"  Mean Judge Score: {bundle.summary['mean_judge_score']:.2f}/5.0")

    # 8. Run quality checks and freshness report
    print("\n[8/9] Running data quality checks...")
    quality = run_data_quality_checks(df, settings, "baseline")
    quality_status = "PASSED" if quality["success"] else "FAILED"
    print(f"  Quality Gate: {quality_status}")
    print(f"  Expectations: {quality['successful_expectations']}/{quality['evaluated_expectations']} passed")

    print("\n[9/9] Building freshness report...")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    freshness_status = "FRESH" if freshness["is_fresh"] else "STALE"
    print(f"  Freshness: {freshness_status}")
    print(f"  Stale ratio: {freshness['stale_ratio']*100:.1f}% (threshold: 25%)")

    # Generate report
    print("\n[REPORT] Generating markdown report...")
    source_summary = {
        "records": len(records),
        "cleaned_records": len(df),
        "fetch_date": run_date.isoformat(),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )
    print(f"  Report saved to {settings.paths.baseline_report}")

    print("\n" + "=" * 60)
    print(f"✅ PHASE 1 COMPLETE!")
    print(f"   Hit Rate: {bundle.summary['retrieval_hit_rate']:.2%}")
    print(f"   Quality Gate: {quality_status}")
    print(f"   Freshness: {freshness_status}")
    print("=" * 60)


if __name__ == "__main__":
    main()
