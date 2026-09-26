from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def _normalize_text(value: str | None) -> str:
    """Gom khoang trang thua, bo khoang trang dau/cuoi."""
    return " ".join((value or "").split())


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Bien doi danh sach `PaperRecord` thanh mot `pandas.DataFrame` sach, san sang embed.

    - Chuan hoa title/summary/authors/categories (gom khoang trang thua).
    - Bo qua row thieu paper_id/title/summary hoac khong parse duoc `published`.
    - Tinh `age_days = (run_date - published).days`.
    - Tao cot helper: authors_joined, categories_joined, summary_chars, text_for_embedding.
    - Khu trung lap theo `paper_id`, sort theo ngay xuat ban moi nhat truoc.
    """
    rows: list[dict] = []

    for record in records:
        paper_id = (record.paper_id or "").strip()
        title = _normalize_text(record.title)
        summary = _normalize_text(record.summary)
        authors = [author for author in (_normalize_text(a) for a in record.authors) if author]
        categories = [cat for cat in (_normalize_text(c) for c in record.categories) if cat]

        if not paper_id or not title or not summary:
            continue

        try:
            published_date = datetime.strptime(record.published, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        age_days = (run_date.date() - published_date).days
        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)

        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {record.published}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": _normalize_text(record.primary_category),
                "published": record.published,
                "updated": record.updated,
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset="paper_id", keep="first")
    df = df.sort_values("published", ascending=False).reset_index(drop=True)
    return df
