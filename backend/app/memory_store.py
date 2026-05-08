from __future__ import annotations

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from app.core.config import settings
from app.services.embeddings import embed_text

log = logging.getLogger("app")


@dataclass
class DocChunk:
    id: int
    source_name: str
    page_number: int | None
    section: str | None
    chunk_index: int
    content: str
    embedding: list[float] | None


@dataclass
class DemoStore:
    movies: list[dict[str, Any]] = field(default_factory=list)
    viewers: list[dict[str, Any]] = field(default_factory=list)
    watch_activity: list[dict[str, Any]] = field(default_factory=list)
    reviews: list[dict[str, Any]] = field(default_factory=list)
    marketing_spend: list[dict[str, Any]] = field(default_factory=list)
    regional_performance: list[dict[str, Any]] = field(default_factory=list)
    chunks: list[DocChunk] = field(default_factory=list)


_store: DemoStore | None = None


def backend_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_demo_store() -> DemoStore:
    if _store is None:
        raise RuntimeError("Demo data not loaded yet")
    return _store


def set_demo_store(store: DemoStore) -> None:
    global _store
    _store = store


def _parse_dt(value: str) -> datetime:
    value = value.strip()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%d")


def _read_csv_table(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


def _detect_heading(line: str) -> str | None:
    line = line.strip()
    if not line or len(line) > 120:
        return None
    if line.isupper() and len(line.split()) <= 12:
        return line.title()
    m = re.match(r"^(\d+\.)?\s*([A-Z][^:]{2,80}):\s*$", line)
    if m:
        return m.group(2).strip() if m.group(2) else None
    if re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+){0,6}$", line) and len(line.split()) <= 8:
        return line
    return None


def _semantic_chunks(page_text: str, *, max_chunk: int = 1400, overlap: int = 200) -> list[tuple[str | None, str]]:
    raw = page_text.replace("\r\n", "\n").strip()
    if not raw:
        return []
    paragraphs = re.split(r"\n\s*\n+", raw)
    current_section: str | None = None
    pieces: list[tuple[str | None, str]] = []
    for p in paragraphs:
        p = " ".join(line.strip() for line in p.split("\n"))
        if not p:
            continue
        head = _detect_heading(p) if len(p) < 160 else None
        if head and len(p) < 160:
            current_section = head
            continue
        pieces.append((current_section, p))
    out: list[tuple[str | None, str]] = []
    for sec, text in pieces:
        i = 0
        t = " ".join(text.split())
        while i < len(t):
            chunk = t[i : i + max_chunk]
            out.append((sec, chunk))
            i += max(1, max_chunk - overlap)
    return out


async def build_demo_store_from_dir(base: Path) -> DemoStore:
    store = DemoStore()

    movie_rows = _read_csv_table(base / "movies.csv")
    for i, r in enumerate(movie_rows, start=1):
        store.movies.append(
            {
                "id": i,
                "title": r["title"],
                "release_year": int(r["release_year"]),
                "genre": r["genre"],
            }
        )

    viewer_rows = _read_csv_table(base / "viewers.csv")
    for i, r in enumerate(viewer_rows, start=1):
        store.viewers.append({"id": i, "city": r["city"], "segment": r["segment"]})

    for r in _read_csv_table(base / "watch_activity.csv"):
        store.watch_activity.append(
            {
                "movie_id": int(r["movie_id"]),
                "viewer_id": int(r["viewer_id"]),
                "watched_at": _parse_dt(r["watched_at"]),
                "minutes_watched": int(r["minutes_watched"]),
            }
        )

    for r in _read_csv_table(base / "reviews.csv"):
        store.reviews.append(
            {
                "movie_id": int(r["movie_id"]),
                "rating": float(r["rating"]),
                "review_text": r["review_text"],
            }
        )

    for r in _read_csv_table(base / "marketing_spend.csv"):
        store.marketing_spend.append(
            {
                "title": r["title"],
                "date": _parse_dt(r["date"]),
                "spend_usd": float(r["spend_usd"]),
            }
        )

    for r in _read_csv_table(base / "regional_performance.csv"):
        store.regional_performance.append(
            {
                "city": r["city"],
                "date": _parse_dt(r["date"]),
                "engagement_score": float(r["engagement_score"]),
            }
        )

    chunk_id = 0
    pdf_dir = base / "pdfs"
    if pdf_dir.is_dir():
        for path in sorted(pdf_dir.glob("*.pdf")):
            try:
                reader = PdfReader(io.BytesIO(path.read_bytes()))
                source = path.stem
                idx = 0
                for page_number, page in enumerate(reader.pages, start=1):
                    page_text = page.extract_text() or ""
                    for section, ch in _semantic_chunks(page_text):
                        chunk_id += 1
                        emb = await embed_text(ch)
                        store.chunks.append(
                            DocChunk(
                                id=chunk_id,
                                source_name=source,
                                page_number=page_number,
                                section=section,
                                chunk_index=idx,
                                content=ch,
                                embedding=emb,
                            )
                        )
                        idx += 1
            except Exception as e:
                log.warning("pdf ingest skipped %s: %s", path.name, e)

    return store


async def load_demo_data_at_startup(*, force: bool = False) -> dict[str, Any]:
    """Load CSV + PDF from backend/demo_data into memory. No database."""
    global _store
    if _store is not None and not force:
        return {"skipped": True, "reason": "already loaded"}
    if force:
        _store = None

    base = backend_root() / settings.demo_data_dir
    if not base.is_dir():
        log.warning("demo_data directory missing: %s", base)
        set_demo_store(DemoStore())
        return {"error": f"missing {base}", "loaded": False}

    store = await build_demo_store_from_dir(base)
    set_demo_store(store)
    log.info(
        "demo store loaded movies=%s viewers=%s chunks=%s",
        len(store.movies),
        len(store.viewers),
        len(store.chunks),
    )
    return {
        "loaded": True,
        "demo_data_dir": str(base),
        "movies": len(store.movies),
        "viewers": len(store.viewers),
        "watch_activity": len(store.watch_activity),
        "reviews": len(store.reviews),
        "marketing_spend": len(store.marketing_spend),
        "regional_performance": len(store.regional_performance),
        "pdf_chunks": len(store.chunks),
    }
