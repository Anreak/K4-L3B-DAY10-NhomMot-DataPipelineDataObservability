from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

_QUESTION_TYPES = ("summary", "authors", "date", "categories")
_TEST_SET_SIZE = 10


def _first_sentence(text: str) -> str:
    """Lay cau dau tien cua tom tat lam ground truth ngan gon."""
    head = text.split(". ")[0].strip()
    if head and not head.endswith("."):
        head += "."
    return head


def _build_question(question_type: str, row: pd.Series) -> tuple[str, str]:
    """Tra ve (question, ground_truth) theo tung dang bai toan."""
    title = row["title"]

    if question_type == "summary":
        return (
            f"What is the summary of the paper '{title}'?",
            _first_sentence(row["summary"]),
        )
    if question_type == "authors":
        return (
            f"Who are the authors of the paper '{title}'?",
            row["authors_joined"],
        )
    if question_type == "date":
        return (
            f"When was the paper '{title}' published?",
            row["published"],
        )
    if question_type == "categories":
        return (
            f"What is the primary research field of the paper '{title}'?",
            row["primary_category"],
        )
    raise ValueError(f"Unsupported question_type: {question_type}")


def build_test_set(df: pd.DataFrame, output_path: Path) -> list[dict[str, Any]]:
    """Sinh bo Benchmark Test Set (Ground Truth) tu cleaned dataframe.

    Chon `_TEST_SET_SIZE` bai bao dau tien (df da duoc sort trong `build_clean_dataframe`)
    va rai deu 4 dang cau hoi (summary/authors/date/categories) theo vong tron,
    moi cau gan voi dung 1 paper_id lam `ground_truth_doc_ids`.
    """
    if len(df) < _TEST_SET_SIZE:
        raise ValueError(
            f"Can it nhat {_TEST_SET_SIZE} bai bao de tao test set, hien co {len(df)}."
        )

    selected = df.head(_TEST_SET_SIZE).reset_index(drop=True)

    test_set: list[dict[str, Any]] = []
    for i, row in selected.iterrows():
        question_type = _QUESTION_TYPES[i % len(_QUESTION_TYPES)]
        question, ground_truth = _build_question(question_type, row)

        test_set.append(
            {
                "id": f"eval_{i + 1:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [row["paper_id"]],
            }
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(test_set, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return test_set
