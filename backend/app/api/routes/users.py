from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.core.security import Principal
from app.schemas.auth import CreateUserRequest, CreateUserResponse
from app.services.auth_sqlite import create_user_record

log = logging.getLogger("app.users")

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=CreateUserResponse)
async def create_user(
    body: CreateUserRequest,
    _admin: Principal = Depends(require_admin),
) -> CreateUserResponse:
    try:
        created = create_user_record(
            email=str(body.email),
            first_name=body.first_name,
            last_name=body.last_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not created:
        raise HTTPException(status_code=409, detail="A user with this email already exists")
    email, temp_pw = created
    log.info("admin created user email=%s", email)
    return CreateUserResponse(
        email=email,
        first_name=body.first_name.strip(),
        last_name=body.last_name.strip(),
        temporary_password=temp_pw,
    )
