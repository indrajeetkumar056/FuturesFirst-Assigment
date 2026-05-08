from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_principal
from app.core.security import Principal

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
def get_history(
    limit: int = Query(20, ge=1, le=200),
    _principal: Principal = Depends(get_principal),
):
    return {"items": [], "note": "No server-side chat history (in-memory demo only)"}
