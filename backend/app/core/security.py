from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import jwt

from app.core.config import settings


@dataclass(frozen=True)
class Principal:
    subject: str
    scopes: list[str]


def _now() -> int:
    return int(time.time())


def mint_access_token(*, principal: Principal) -> str:
    now = _now()
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": principal.subject,
        "scopes": principal.scopes,
        "iat": now,
        "nbf": now - max(0, settings.jwt_nbf_skew_seconds),
        "exp": now + max(1, settings.jwt_ttl_seconds),
        # unique-per-request token (helps rotation semantics)
        "jti": f"{principal.subject}:{now}:{time.time_ns()}",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def verify_access_token(token: str) -> Principal:
    decoded = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_alg],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        leeway=60,
        options={
            "require": ["exp", "iat", "nbf", "sub", "iss", "aud"],
        },
    )
    sub = str(decoded.get("sub"))
    scopes = decoded.get("scopes") or []
    if not isinstance(scopes, list) or any(not isinstance(s, str) for s in scopes):
        raise jwt.InvalidTokenError("Invalid scopes")
    return Principal(subject=sub, scopes=scopes)


def parse_bearer_token(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None
