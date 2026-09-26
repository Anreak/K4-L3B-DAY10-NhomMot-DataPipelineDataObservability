from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

from core.config import Settings

CROSSREF_API_URL = "https://api.crossref.org/works"
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 2.0

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(raw: str | None) -> str:
    """Bo the HTML/XML (vd <jats:p>) va gom khoang trang thua."""
    if not raw:
        return ""
    without_tags = _TAG_RE.sub(" ", raw)
    return _WHITESPACE_RE.sub(" ", without_tags).strip()


def _format_date(date_parts: list[int] | None) -> str:
    """Chuan hoa Crossref `date-parts` ([year, month, day]) thanh chuoi YYYY-MM-DD."""
    if not date_parts:
        return ""
    padded = list(date_parts) + [1, 1]
    year, month, day = padded[0], padded[1], padded[2]
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Boc tach cau truc payload JSON tu Crossref API thanh danh sach `PaperRecord`.

    Bo qua cac item khong co DOI hoac title vi day la 2 truong bat buoc
    dung lam paper_id / noi dung chinh cho pipeline phia sau.
    """
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = item.get("DOI")
        titles = item.get("title") or []
        if not doi or not titles:
            continue

        authors = [
            _clean_text(f"{author.get('given', '')} {author.get('family', '')}")
            for author in item.get("author", [])
        ]
        authors = [author for author in authors if author]

        categories = item.get("subject") or []
        primary_category = categories[0] if categories else ""

        published = _format_date((item.get("published") or {}).get("date-parts", [[]])[0])
        created_date_time = (item.get("created") or {}).get("date-time", "")
        updated = created_date_time[:10] if created_date_time else published

        url = item.get("URL", "")

        records.append(
            PaperRecord(
                paper_id=doi,
                title=_clean_text(titles[0]),
                summary=_clean_text(item.get("abstract")),
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=url,
                pdf_url=url,
                comment=f"Crossref record {doi}",
            )
        )

    return records


def _fetch_crossref_payload(settings: Settings) -> dict | None:
    """Goi Crossref REST API voi retry cho 429/5xx. Tra ve None neu that bai
    (mat mang hoac het luot retry) de caller fallback ve snapshot local."""
    params = {
        "query.bibliographic": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = requests.get(CROSSREF_API_URL, params=params, timeout=15)
        except requests.RequestException:
            return None

        if response.status_code == 200:
            return response.json()

        if response.status_code in _RETRYABLE_STATUS_CODES and attempt < _MAX_ATTEMPTS:
            time.sleep(_BACKOFF_SECONDS * attempt)
            continue

        return None

    return None


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi Crossref API (hoac fallback doc snapshot), luu 2 raw artifacts va tra ve records.

    1. Neu `refresh_source=True` hoac chua co snapshot -> goi API.
    2. Neu API that bai (mat mang / 429 / 5xx het retry) -> doc snapshot local
       tai `settings.paths.raw_api_response` (neu co).
    3. Luu payload goc vao `raw_api_response` va records da parse vao `raw_records_json`.
    """
    raw_path = settings.paths.raw_api_response
    records_path = settings.paths.raw_records_json

    payload = None
    if settings.refresh_source or not raw_path.exists():
        payload = _fetch_crossref_payload(settings)
        if payload is not None:
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if payload is None:
        if not raw_path.exists():
            raise RuntimeError(
                f"Khong the goi Crossref API va khong tim thay snapshot du phong tai {raw_path}."
            )
        payload = json.loads(raw_path.read_text(encoding="utf-8"))

    records = parse_crossref_payload(payload)

    records_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.write_text(
        json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot (list cac dict theo schema PaperRecord) va map thanh `PaperRecord`."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [PaperRecord(**item) for item in data]
