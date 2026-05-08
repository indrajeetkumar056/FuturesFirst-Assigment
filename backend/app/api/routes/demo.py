from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_principal
from app.core.security import Principal
from app.memory_store import load_demo_data_at_startup

log = logging.getLogger("app.demo")

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/reload")
async def reload_demo(_principal: Principal = Depends(get_principal)):
    """Reload CSV + PDF from demo_data/ into memory (no database)."""
    log.info("demo reload requested subject=%s", _principal.subject)
    result = await load_demo_data_at_startup(force=True)
    log.info("demo reload result=%s", result)
    return result
