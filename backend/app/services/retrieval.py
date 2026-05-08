from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np

from app.memory_store import DemoStore, DocChunk
from app.services.embeddings import embed_text


@dataclass(frozen=True)
class RetrievalHit:
    chunk: DocChunk
    score: float
    vector_score: float | None = None
    keyword_score: float | None = None


def _tokenize_q(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z0-9]{2,}", text.lower()) if len(t) > 1}


def _lexical_boost(query: str, content: str, hybrid_score: float) -> float:
    qtok = _tokenize_q(query)
    if not qtok:
        return hybrid_score
    ctok = _tokenize_q(content)
    overlap = len(qtok & ctok) / max(len(qtok), 1)
    return hybrid_score * (1.0 + 0.35 * overlap)


def _tf(tokens: list[str]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = float(len(tokens) or 1)
    return {k: v / total for k, v in counts.items()}


def _cosine_bow(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, av in a.items():
        bv = b.get(k)
        if bv is not None:
            dot += av * bv
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _cosine_emb(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    aa = np.asarray(a, dtype=np.float64)
    bb = np.asarray(b, dtype=np.float64)
    na = np.linalg.norm(aa)
    nb = np.linalg.norm(bb)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(aa, bb) / (na * nb))


async def search_docs_hybrid(
    store: DemoStore,
    *,
    query: str,
    limit: int = 5,
) -> list[RetrievalHit]:
    q_emb = await embed_text(query)
    q_bow = _tf(list(_tokenize_q(query)))
    hits: list[RetrievalHit] = []
    for ch in store.chunks:
        tokens = list(_tokenize_q(ch.content))
        kscore = _cosine_bow(q_bow, _tf(tokens))
        vscore: float | None = None
        emb = ch.embedding
        if isinstance(emb, list) and emb:
            try:
                vec = [float(x) for x in emb]
                if len(vec) == len(q_emb):
                    vscore = _cosine_emb(q_emb, vec)
            except (TypeError, ValueError):
                vscore = None
        if vscore is not None and vscore > 0:
            hybrid = (0.65 * max(0.0, min(1.0, vscore))) + (0.35 * kscore)
        else:
            hybrid = kscore
        final = _lexical_boost(query, ch.content, hybrid)
        hits.append(RetrievalHit(chunk=ch, score=final, vector_score=vscore, keyword_score=kscore))
    hits.sort(key=lambda h: h.score, reverse=True)
    return [h for h in hits[:limit] if h.score > 0]


async def search_docs(store: DemoStore, *, query: str, limit: int = 5) -> list[DocChunk]:
    hits = await search_docs_hybrid(store, query=query, limit=limit)
    return [h.chunk for h in hits]
