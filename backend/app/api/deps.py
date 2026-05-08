from __future__ import annotations

import logging

from fastapi import Depends, Header, HTTPException

from app.core.security import Principal, parse_bearer_token, verify_access_token
from app.memory_store import DemoStore, get_demo_store

log = logging.getLogger("app.deps")


def get_principal(authorization: str | None = Header(default=None)) -> Principal:
    token = parse_bearer_token(authorization)
    if not token:
        log.debug("auth missing Authorization bearer")
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return verify_access_token(token)
    except Exception as e:
        log.warning("auth invalid token: %s", type(e).__name__)
        raise HTTPException(status_code=401, detail="Invalid token") from e


def require_admin(principal: Principal = Depends(get_principal)) -> Principal:
    if "admin" not in principal.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")
    return principal


def get_store() -> DemoStore:
    try:
        return get_demo_store()
    except RuntimeError as e:
        log.warning("demo store unavailable: %s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e
