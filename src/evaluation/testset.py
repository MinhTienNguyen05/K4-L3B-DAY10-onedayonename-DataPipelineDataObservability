from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path: str | Path) -> list[dict[str, Any]]:
    """Build a benchmark test set of 10 ground truth questions across 4 question types.

    Question Distribution (10 questions):
    - 3 summary: "What is the summary of the paper '<Title>'?"
    - 3 authors: "Who authored the paper '<Title>'?"
    - 2 date: "When was the paper '<Title>' published?"
    - 2 categories: "What categories does the paper '<Title>' belong to?"

    Schema per item:
    {
        "id": "eval_001",
        "question_type": "summary",
        "question": "...",
        "ground_truth": "...",
        "ground_truth_doc_ids": ["..."]
    }
    """
    if df.empty:
        write_json(Path(output_path), [])
        return []

    records = df.to_dict(orient="records")
    n_docs = len(records)
    
    # 10 questions configuration: (type, question_template, ground_truth_extractor)
    configs = [
        # 3 Summary questions
        ("summary", "What is the summary of the paper '{title}'?", lambda r: first_sentence(str(r.get("summary", "")))),
        ("summary", "What is the summary of the paper '{title}'?", lambda r: first_sentence(str(r.get("summary", "")))),
        ("summary", "What is the summary of the paper '{title}'?", lambda r: first_sentence(str(r.get("summary", "")))),
        # 3 Authors questions
        ("authors", "Who authored the paper '{title}'?", lambda r: str(r.get("authors_joined") or (", ".join(r.get("authors", [])) if isinstance(r.get("authors"), list) else str(r.get("authors", ""))))),
        ("authors", "Who authored the paper '{title}'?", lambda r: str(r.get("authors_joined") or (", ".join(r.get("authors", [])) if isinstance(r.get("authors"), list) else str(r.get("authors", ""))))),
        ("authors", "Who authored the paper '{title}'?", lambda r: str(r.get("authors_joined") or (", ".join(r.get("authors", [])) if isinstance(r.get("authors"), list) else str(r.get("authors", ""))))),
        # 2 Date questions
        ("date", "When was the paper '{title}' published?", lambda r: str(r.get("published", ""))),
        ("date", "When was the paper '{title}' published?", lambda r: str(r.get("published", ""))),
        # 2 Categories questions
        ("categories", "What categories does the paper '{title}' belong to?", lambda r: str(r.get("categories_joined") or (", ".join(r.get("categories", [])) if isinstance(r.get("categories"), list) else str(r.get("categories", ""))))),
        ("categories", "What categories does the paper '{title}' belong to?", lambda r: str(r.get("categories_joined") or (", ".join(r.get("categories", [])) if isinstance(r.get("categories"), list) else str(r.get("categories", ""))))),
    ]

    test_set: list[dict[str, Any]] = []
    for idx, (q_type, tmpl, gt_fn) in enumerate(configs):
        doc = records[idx % n_docs]
        title = doc.get("title", "")
        paper_id = str(doc.get("paper_id", ""))
        
        item = {
            "id": f"eval_{idx + 1:03d}",
            "question_type": q_type,
            "question": tmpl.format(title=title),
            "ground_truth": gt_fn(doc),
            "ground_truth_doc_ids": [paper_id],
        }
        test_set.append(item)

    write_json(Path(output_path), test_set)
    return test_set

