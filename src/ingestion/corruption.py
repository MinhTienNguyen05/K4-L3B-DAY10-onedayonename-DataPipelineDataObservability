from __future__ import annotations

import pandas as pd


from pathlib import Path
from typing import Any

from core.utils import write_json


def _format_text_for_embedding(row: pd.Series | dict[str, Any]) -> str:
    authors = row.get("authors_joined") or (
        ", ".join(row.get("authors", [])) if isinstance(row.get("authors"), list) else str(row.get("authors", ""))
    )
    categories = row.get("categories_joined") or (
        ", ".join(row.get("categories", [])) if isinstance(row.get("categories"), list) else str(row.get("categories", ""))
    )
    return (
        f"Title: {row.get('title', '')}\n"
        f"Authors: {authors}\n"
        f"Published: {row.get('published', '')}\n"
        f"Categories: {categories}\n"
        f"Summary: {row.get('summary', '')}"
    )


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: str | Path) -> pd.DataFrame:
    """Simulate multiple real-world data corruption scenarios for observability evaluation.

    Scenarios:
    1. Drop latest records (drop newest ~20% of records).
    2. Blank summary on ~30% of remaining records.
    3. Inject noisy text ('!!!CORRUPTED NOISE RAG FAILURE!!!') into summaries.
    4. Truncate titles to < 8 chars on selected records.
    5. Stale date: shift published dates back by 365 days and increase age_days.
    6. Duplicate rows: duplicate ~20% of records to create duplicates.
    7. Rebuild `text_for_embedding`.
    8. Write detailed corruption log to output_log_path.
    """
    if df.empty:
        write_json(Path(output_log_path), {"scenarios": [], "total_corrupted": 0})
        return df.copy()

    corrupted = df.copy().reset_index(drop=True)
    n_rows = len(corrupted)
    logs: list[dict[str, Any]] = []

    # 1. Drop latest records (bỏ 20% records mới nhất)
    drop_count = max(1, int(n_rows * 0.2))
    dropped_ids = []
    if "published" in corrupted.columns:
        corrupted = corrupted.sort_values(by="published", ascending=True)
        dropped_ids = corrupted.tail(drop_count)["paper_id"].tolist()
        corrupted = corrupted.iloc[:-drop_count].reset_index(drop=True)
    else:
        dropped_ids = corrupted.tail(drop_count)["paper_id"].tolist()
        corrupted = corrupted.iloc[:-drop_count].reset_index(drop=True)

    logs.append({
        "scenario": "drop_latest_records",
        "dropped_count": drop_count,
        "affected_paper_ids": dropped_ids,
        "description": f"Dropped {drop_count} latest records to simulate stale dataset drop."
    })

    remaining_rows = len(corrupted)

    # 2. Blank summary ở ~30% dòng còn lại
    blank_indices = list(range(0, remaining_rows, 3))
    blanked_ids = []
    for idx in blank_indices:
        corrupted.at[idx, "summary"] = ""
        if "summary_chars" in corrupted.columns:
            corrupted.at[idx, "summary_chars"] = 0
        blanked_ids.append(str(corrupted.at[idx, "paper_id"]))

    logs.append({
        "scenario": "blank_summary",
        "affected_count": len(blanked_ids),
        "affected_paper_ids": blanked_ids,
        "description": f"Set empty summary on {len(blanked_ids)} records to trigger null/length checks."
    })

    # 3. Inject noise vào summary của một số dòng (ví dụ các dòng có index chia hết cho 4)
    noise_indices = [i for i in range(1, remaining_rows, 4) if i not in blank_indices]
    noisy_ids = []
    for idx in noise_indices:
        old_summary = str(corrupted.at[idx, "summary"])
        corrupted.at[idx, "summary"] = f"!!!CORRUPTED NOISE RAG FAILURE!!! {old_summary}"
        if "summary_chars" in corrupted.columns:
            corrupted.at[idx, "summary_chars"] = len(str(corrupted.at[idx, "summary"]))
        noisy_ids.append(str(corrupted.at[idx, "paper_id"]))

    logs.append({
        "scenario": "inject_noise",
        "affected_count": len(noisy_ids),
        "affected_paper_ids": noisy_ids,
        "description": f"Injected synthetic noise into summary for {len(noisy_ids)} records."
    })

    # 4. Truncate title < 8 ký tự
    trunc_indices = [i for i in range(2, min(5, remaining_rows))]
    truncated_ids = []
    for idx in trunc_indices:
        old_title = str(corrupted.at[idx, "title"])
        corrupted.at[idx, "title"] = old_title[:6] if len(old_title) >= 6 else "Bad"
        truncated_ids.append(str(corrupted.at[idx, "paper_id"]))

    logs.append({
        "scenario": "truncate_title",
        "affected_count": len(truncated_ids),
        "affected_paper_ids": truncated_ids,
        "description": f"Truncated titles to < 8 chars for {len(truncated_ids)} records."
    })

    # 5. Stale date: Lùi published về 365 ngày trước (tăng age_days lên +365)
    stale_indices = [i for i in range(min(4, remaining_rows))]
    stale_ids = []
    for idx in stale_indices:
        corrupted.at[idx, "published"] = "2024-01-01"
        if "age_days" in corrupted.columns:
            corrupted.at[idx, "age_days"] = int(corrupted.at[idx, "age_days"] or 0) + 365
        stale_ids.append(str(corrupted.at[idx, "paper_id"]))

    logs.append({
        "scenario": "stale_date",
        "affected_count": len(stale_ids),
        "affected_paper_ids": stale_ids,
        "description": f"Shifted publication dates back to simulate SLA violation for {len(stale_ids)} records."
    })

    # 6. Duplicate rows: nhân đôi ~20% records
    dup_count = max(1, int(remaining_rows * 0.2))
    dup_rows = corrupted.head(dup_count).copy()
    corrupted = pd.concat([corrupted, dup_rows], ignore_index=True)

    logs.append({
        "scenario": "duplicate_rows",
        "affected_count": dup_count,
        "affected_paper_ids": dup_rows["paper_id"].tolist(),
        "description": f"Duplicated {dup_count} records to test uniqueness expectation."
    })

    # 7. Rebuild `text_for_embedding`
    corrupted["text_for_embedding"] = corrupted.apply(_format_text_for_embedding, axis=1)

    # 8. Ghi corruption log vào output_log_path
    log_payload = {
        "total_initial_records": n_rows,
        "total_corrupted_records": len(corrupted),
        "scenarios": logs,
    }
    write_json(Path(output_log_path), log_payload)

    return corrupted

