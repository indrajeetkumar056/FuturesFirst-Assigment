from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.config import settings

log = logging.getLogger("app.errors")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _with_request_id(payload: dict, request: Request) -> dict:
    rid = _request_id(request)
    if rid:
        return {**payload, "request_id": rid}
    return payload


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    rid = _request_id(request)
    if exc.status_code >= 500:
        log.error("HTTP %s %s: %s", exc.status_code, request.url.path, exc.detail, extra={"request_id": rid})
    elif exc.status_code >= 400:
        log.warning("HTTP %s %s: %s", exc.status_code, request.url.path, exc.detail, extra={"request_id": rid})
    body: dict = {
        "error": "http_error",
        "detail": exc.detail if isinstance(exc.detail, str) else exc.detail,
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=_with_request_id(body, request),
        headers=getattr(exc, "headers", None),
    )


async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    rid = _request_id(request)
    log.warning(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
        extra={"request_id": rid},
    )
    body = {
        "error": "validation_error",
        "message": "Request validation failed",
        "details": exc.errors(),
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_with_request_id(body, request),
    )


async def pydantic_validation_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    rid = _request_id(request)
    log.warning(
        "Pydantic validation error on %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
        extra={"request_id": rid},
    )
    body = {
        "error": "validation_error",
        "message": "Data validation failed",
        "details": exc.errors(),
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_with_request_id(body, request),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    rid = _request_id(request) or str(uuid.uuid4())
    log.exception("Unhandled error on %s %s", request.method, request.url.path, extra={"request_id": rid})
    detail = str(exc) if settings.app_env.lower() in ("dev", "development", "local") else None
    body: dict = {
        "error": "internal_error",
        "message": "An unexpected error occurred",
    }
    if detail:
        body["debug_detail"] = detail
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_with_request_id(body, request),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
