from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def _normalize_login_email(v: str) -> str:
    """Allow local dev addresses like user@localhost (RFC-style EmailStr rejects these)."""
    s = v.strip().lower()
    if not s or len(s) > 254:
        raise ValueError("invalid email")
    if s.count("@") != 1:
        raise ValueError("invalid email")
    local, domain = s.split("@", 1)
    if not local or not domain:
        raise ValueError("invalid email")
    if ".." in local or ".." in domain:
        raise ValueError("invalid email")
    return s


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def email_ok(cls, v: str) -> str:
        return _normalize_login_email(v)


class CreateUserRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def email_ok(cls, v: str) -> str:
        return _normalize_login_email(v)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be empty")
        return s


class CreateUserResponse(BaseModel):
    email: str
    first_name: str
    last_name: str
    temporary_password: str
