from __future__ import annotations

import asyncio
import hashlib
import logging
from functools import lru_cache
from typing import Any

import numpy as np

from app.core.config import settings

log = logging.getLogger("app.embeddings")

_st_model: Any = None


@lru_cache(maxsize=1)
def _dims() -> int:
    return int(settings.embedding_dimensions)


def _local_hash_embedding(text: str) -> list[float]:
    """Deterministic fallback when ST/OpenAI embeddings are disabled or fail."""
    d = _dims()
    vec = np.zeros((d,), dtype=np.float32)
    for token in text.lower().split():
        h = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "little") % d
        vec[idx] += 1.0
    norm = float(np.linalg.norm(vec) or 1.0)
    vec = vec / norm
    return vec.astype(float).tolist()


def _get_sentence_transformer():
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer

        log.info(
            "Loading SentenceTransformer model=%s (first run may download weights)",
            settings.embedding_model,
        )
        _st_model = SentenceTransformer(settings.embedding_model)
        try:
            actual = int(_st_model.get_sentence_embedding_dimension())
        except Exception:
            actual = None
        if actual is not None and actual != _dims():
            log.warning(
                "EMBEDDING_DIMENSIONS=%s but model reports %s — update .env for accurate hybrid retrieval",
                _dims(),
                actual,
            )
    return _st_model


def _embed_sentence_transformer_sync(text: str) -> list[float]:
    model = _get_sentence_transformer()
    emb = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return [float(x) for x in np.asarray(emb, dtype=np.float64).ravel()]


async def _embed_sentence_transformer(text: str) -> list[float]:
    try:
        return await asyncio.to_thread(_embed_sentence_transformer_sync, text)
    except Exception as e:
        log.exception("sentence-transformers encode failed: %s", e)
        return _local_hash_embedding(text)


def _embed_openai_sync(text: str) -> list[float]:
    from openai import OpenAI

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    resp = client.embeddings.create(model=settings.embedding_model, input=text)
    return [float(x) for x in resp.data[0].embedding]


async def _embed_openai(text: str) -> list[float]:
    try:
        return await asyncio.to_thread(_embed_openai_sync, text)
    except Exception as e:
        log.warning("OpenAI embedding failed, using hash fallback: %s", type(e).__name__)
        return _local_hash_embedding(text)


async def embed_text(text: str) -> list[float]:
    if not (text and text.strip()):
        return _local_hash_embedding(text)

    p = settings.embedding_provider.lower().strip()

    if p in ("sentence_transformers", "sentence-transformers", "st", "minilm"):
        return await _embed_sentence_transformer(text.strip())

    if p == "openai":
        return await _embed_openai(text.strip())

    if p in ("local_hash", "hash"):
        return _local_hash_embedding(text.strip())

    log.warning("unknown EMBEDDING_PROVIDER=%r; using sentence_transformers", settings.embedding_provider)
    return await _embed_sentence_transformer(text.strip())
