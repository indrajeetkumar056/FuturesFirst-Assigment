from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_principal, get_store
from app.core.security import Principal
from app.memory_store import DemoStore
from app.services.retrieval import search_docs

router = APIRouter(prefix="/docs", tags=["docs"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, max_length=2000),
    limit: int = Query(5, ge=1, le=20),
    _principal: Principal = Depends(get_principal),
    store: DemoStore = Depends(get_store),
):
    chunks = await search_docs(store, query=q, limit=limit)
    return {
        "query": q,
        "chunks": [
            {
                "id": c.id,
                "source_name": c.source_name,
                "page_number": c.page_number,
                "section": c.section,
                "content": c.content[:1200],
            }
            for c in chunks
        ],
    }
