from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Build corruption -> evaluate -> repair -> compare flow.

    Steps:
    1. Load settings and baseline metrics.
    2. Create corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index and evaluate.
    5. Run quality checks/freshness on corrupted data.
    6. Repair from raw records.
    7. Evaluate repaired dataset.
    8. Generate comparison report.
    """
    print("=" * 60)
    print("CORRUPTION FLOW: BASELINE -> CORRUPTED -> REPAIRED")
    print("=" * 60)

    # 1. Load settings
    settings = load_settings()
    print("\n[1/8] Settings loaded.")

    # Load baseline metrics
    print("\n[2/8] Loading baseline data...")
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_df = pd.read_json(settings.paths.clean_json)
    print(f"  Baseline metrics loaded. {len(baseline_df)} records in clean dataset.")

    # 2. Corrupt data
    print("\n[3/8] Corrupting data...")
    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    print(f"  Created {len(corrupted_df)} corrupted records.")
    print(f"  Corruption log saved to {settings.paths.corruption_log}")

    # 3. Save corrupted artifacts
    print("\n[4/8] Saving corrupted artifacts...")
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    print(f"  Saved to {settings.paths.corrupted_clean_json} and {settings.paths.corrupted_clean_csv}")

    # 4. Build corrupted index and evaluate
    print("\n[5/8] Building corrupted index and evaluating...")
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, settings.paths.corrupted_embeddings_json
    )
    print(f"  Indexed {len(corrupted_index.documents)} documents in corrupted collection.")

    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f"  Corrupted Hit Rate: {corrupted_bundle.summary['retrieval_hit_rate']:.2%}")
    print(f"  Corrupted Mean Token F1: {corrupted_bundle.summary['mean_token_f1']:.4f}")
    print(f"  Corrupted Judge Accuracy: {corrupted_bundle.summary['judge_accuracy']:.2%}")
    print(f"  Corrupted Mean Judge Score: {corrupted_bundle.summary['mean_judge_score']:.2f}/5.0")

    # 5. Run quality checks on corrupted data
    print("\n[6/8] Running quality checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_quality_status = "PASSED" if corrupted_quality["success"] else "FAILED"
    print(f"  Corrupted Quality Gate: {corrupted_quality_status}")
    print(f"  Expectations: {corrupted_quality['successful_expectations']}/{corrupted_quality['evaluated_expectations']} passed")

    corrupted_freshness = build_freshness_report(corrupted_df, settings, settings.paths.freshness_report)
    corrupted_freshness_status = "FRESH" if corrupted_freshness["is_fresh"] else "STALE"
    print(f"  Corrupted Freshness: {corrupted_freshness_status}")

    # 6. Repair from raw records
    print("\n[7/8] Repairing data from raw records...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, now_utc())
    print(f"  Repaired {len(repaired_df)} records.")

    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    print(f"  Saved repaired artifacts.")

    # Build repaired index and evaluate
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, settings.paths.repaired_embeddings_json
    )
    print(f"  Indexed {len(repaired_index.documents)} documents in repaired collection.")

    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print(f"  Repaired Hit Rate: {repaired_bundle.summary['retrieval_hit_rate']:.2%}")
    print(f"  Repaired Mean Token F1: {repaired_bundle.summary['mean_token_f1']:.4f}")
    print(f"  Repaired Judge Accuracy: {repaired_bundle.summary['judge_accuracy']:.2%}")
    print(f"  Repaired Mean Judge Score: {repaired_bundle.summary['mean_judge_score']:.2f}/5.0")

    # Run quality checks on repaired data
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_quality_status = "PASSED" if repaired_quality["success"] else "FAILED"
    print(f"  Repaired Quality Gate: {repaired_quality_status}")

    repaired_freshness = build_freshness_report(repaired_df, settings, settings.paths.freshness_report)
    repaired_freshness_status = "FRESH" if repaired_freshness["is_fresh"] else "STALE"
    print(f"  Repaired Freshness: {repaired_freshness_status}")

    # 8. Generate comparison report
    print("\n[8/8] Generating comparison report...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"  Report saved to {settings.paths.comparison_report}")

    # Summary comparison table
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"{'Metric':<25} {'Baseline':>12} {'Corrupted':>12} {'Repaired':>12}")
    print("-" * 60)
    print(f"{'Hit Rate':<25} {baseline_metrics['retrieval_hit_rate']:>11.2%} {corrupted_bundle.summary['retrieval_hit_rate']:>11.2%} {repaired_bundle.summary['retrieval_hit_rate']:>11.2%}")
    print(f"{'Mean Token F1':<25} {baseline_metrics['mean_token_f1']:>12.4f} {corrupted_bundle.summary['mean_token_f1']:>12.4f} {repaired_bundle.summary['mean_token_f1']:>12.4f}")
    print(f"{'Judge Accuracy':<25} {baseline_metrics['judge_accuracy']:>11.2%} {corrupted_bundle.summary['judge_accuracy']:>11.2%} {repaired_bundle.summary['judge_accuracy']:>11.2%}")
    print(f"{'Mean Judge Score':<25} {baseline_metrics['mean_judge_score']:>12.2f} {corrupted_bundle.summary['mean_judge_score']:>12.2f} {repaired_bundle.summary['mean_judge_score']:>12.2f}")
    print("-" * 60)
    print(f"{'Quality Gate':<25} {'PASSED':>12} {corrupted_quality_status:>12} {repaired_quality_status:>12}")
    print(f"{'Freshness':<25} {'FRESH':>12} {corrupted_freshness_status:>12} {repaired_freshness_status:>12}")
    print("=" * 60)
    print("✅ CORRUPTION FLOW COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
