from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate 6 dang data corruption thuc te:
    1. Drop latest records: Bo 20% cac bai bao moi nhat.
    2. Blank summary: Xoa trang phan tom tat o mot so dong.
    3. Inject noise: Chen chuoi ky tu rac vao tom tat.
    4. Truncate title: Cat ngan tieu de xuong duoi 8 ky tu.
    5. Stale date: Lui ngay xuat ban ve 365 ngay truoc.
    6. Duplicate rows: Nhan doi cac dong de tao trung lap paper_id.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vao output_log_path.
    """
    corrupted_df = df.copy()
    corruption_log: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "original_rows": len(df),
        "corruptions": {},
    }

    # 1. Drop latest records: Bo 20% cac bai bao moi nhat
    sorted_df = corrupted_df.sort_values(by="published", ascending=False)
    n_drop = max(1, int(len(corrupted_df) * 0.20))
    dropped_ids = sorted_df.iloc[:n_drop]["paper_id"].tolist()
    corrupted_df = corrupted_df[~corrupted_df["paper_id"].isin(dropped_ids)].copy().reset_index(drop=True)
    corruption_log["corruptions"]["drop_latest_records"] = {
        "count": len(dropped_ids),
        "percentage": 20,
        "dropped_paper_ids": dropped_ids,
    }

    # 2. Blank summary: Xoa trang tom tat o 2 dong
    blank_summary_ids = []
    if len(corrupted_df) >= 2:
        for idx in range(min(2, len(corrupted_df))):
            pid = corrupted_df.at[idx, "paper_id"]
            blank_summary_ids.append(pid)
            corrupted_df.at[idx, "summary"] = ""
            corrupted_df.at[idx, "summary_chars"] = 0
    corruption_log["corruptions"]["blank_summary"] = {
        "count": len(blank_summary_ids),
        "affected_paper_ids": blank_summary_ids,
    }

    # 3. Inject noise: Chen cac chuoi ky tu rac vao tom tat
    noise_ids = []
    noise_string = " [NOISE_CORRUPTION_#@$%*&_RANDOM_TEXT_UNRELATED_METADATA_CHUNK] "
    if len(corrupted_df) >= 4:
        for idx in range(2, min(4, len(corrupted_df))):
            pid = corrupted_df.at[idx, "paper_id"]
            noise_ids.append(pid)
            original_summary = corrupted_df.at[idx, "summary"]
            corrupted_df.at[idx, "summary"] = noise_string + str(original_summary) + noise_string
            corrupted_df.at[idx, "summary_chars"] = len(corrupted_df.at[idx, "summary"])
    corruption_log["corruptions"]["inject_noise"] = {
        "count": len(noise_ids),
        "affected_paper_ids": noise_ids,
    }

    # 4. Truncate title: Cat ngan tieu de xuong duoi 8 ky tu
    truncate_ids = []
    if len(corrupted_df) >= 6:
        for idx in range(4, min(6, len(corrupted_df))):
            pid = corrupted_df.at[idx, "paper_id"]
            truncate_ids.append(pid)
            title = str(corrupted_df.at[idx, "title"])
            corrupted_df.at[idx, "title"] = title[:5].strip() or "Trunc"
    corruption_log["corruptions"]["truncate_title"] = {
        "count": len(truncate_ids),
        "affected_paper_ids": truncate_ids,
    }

    # 5. Stale date: Lui ngay xuat ban ve 365 ngay truoc (>25% dong bi stale)
    stale_ids = []
    stale_target_count = min(8, len(corrupted_df))
    for idx in range(stale_target_count):
        pid = corrupted_df.at[idx, "paper_id"]
        stale_ids.append(pid)
        current_pub = str(corrupted_df.at[idx, "published"])
        try:
            pub_date = datetime.strptime(current_pub[:10], "%Y-%m-%d")
            stale_pub_date = pub_date - timedelta(days=365)
            corrupted_df.at[idx, "published"] = stale_pub_date.strftime("%Y-%m-%d")
        except ValueError:
            corrupted_df.at[idx, "published"] = "2024-01-01"
        corrupted_df.at[idx, "age_days"] = int(corrupted_df.at[idx, "age_days"]) + 365
    corruption_log["corruptions"]["stale_date"] = {
        "count": len(stale_ids),
        "days_shifted": 365,
        "affected_paper_ids": stale_ids,
    }

    # 6. Duplicate rows: Nhan doi 2 dong de tao trung lap paper_id
    duplicate_ids = []
    if len(corrupted_df) >= 2:
        dup_rows = corrupted_df.iloc[:2].copy()
        duplicate_ids = dup_rows["paper_id"].tolist()
        corrupted_df = pd.concat([corrupted_df, dup_rows], ignore_index=True)
    corruption_log["corruptions"]["duplicate_rows"] = {
        "count": len(duplicate_ids),
        "duplicated_paper_ids": duplicate_ids,
    }

    # 7. Rebuild text_for_embedding
    rebuilt_texts = []
    for _, row in corrupted_df.iterrows():
        t = (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Published: {row['published']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Summary: {row['summary']}"
        )
        rebuilt_texts.append(t)
    corrupted_df["text_for_embedding"] = rebuilt_texts

    corruption_log["corrupted_rows_total"] = len(corrupted_df)

    out_file = Path(output_log_path)
    write_json(out_file, corruption_log)
    return corrupted_df
