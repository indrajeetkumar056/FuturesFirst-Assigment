from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None

