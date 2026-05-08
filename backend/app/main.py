from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.security import Principal, mint_access_token, parse_bearer_token, verify_access_token
from app.memory_store import load_demo_data_at_startup
from app.middleware.request_context import RequestContextMiddleware
from app.schemas.auth import LoginRequest
from app.services.auth_sqlite import authenticate_user, init_auth_db

configure_logging(settings.log_level)
log = logging.getLogger("app")

app = FastAPI(title=settings.app_name)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-access-token", "x-request-id"],
)

app.add_middleware(RequestContextMiddleware)


@app.on_event("startup")
async def on_startup() -> None:
    init_auth_db()
    log.info("sqlite auth initialized path=%s", settings.auth_db_path)
    summary = await load_demo_data_at_startup()
    log.info("demo data (in-memory): %s", summary)


@app.middleware("http")
async def jwt_rotate_each_request(request: Request, call_next):
    principal: Principal | None = None
    token = parse_bearer_token(request.headers.get("authorization"))
    if token:
        try:
            principal = verify_access_token(token)
        except Exception:
            principal = None

    response: Response = await call_next(request)
    if principal:
        response.headers["x-access-token"] = mint_access_token(principal=principal)
    return response


@app.post("/auth/login")
async def login(payload: LoginRequest) -> dict:
    user = await asyncio.to_thread(authenticate_user, str(payload.email), payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    scopes = ["admin", "user"] if user["is_admin"] else ["user"]
    token = mint_access_token(
        principal=Principal(subject=user["email"], scopes=scopes),
    )
    log.info("login email=%s admin=%s", user["email"], user["is_admin"])
    return {"access_token": token, "token_type": "bearer"}


app.include_router(api_router)
