from __future__ import annotations

import logging
import secrets
import sqlite3
import threading
from pathlib import Path
from typing import Any

import bcrypt

from app.core.config import settings

log = logging.getLogger("app.auth_sqlite")

_lock = threading.Lock()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _db_path() -> Path:
    raw = Path(settings.auth_db_path)
    if raw.is_absolute():
        return raw
    return Path.cwd() / raw


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db() -> None:
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            conn.commit()
            _ensure_admin(conn)
            conn.commit()
        finally:
            conn.close()


def _ensure_admin(conn: sqlite3.Connection) -> None:
    email = settings.admin_email.strip().lower()
    cur = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cur.fetchone():
        return
    pw = settings.admin_password
    conn.execute(
        """
        INSERT INTO users (email, password_hash, first_name, last_name, is_admin)
        VALUES (?, ?, ?, ?, 1)
        """,
        (email, _hash_password(pw), "Admin", "User"),
    )
    log.info("seeded admin user email=%s", email)


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    key = email.strip().lower()
    if not key or not password:
        return None
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                "SELECT email, password_hash, first_name, last_name, is_admin FROM users WHERE email = ?",
                (key,),
            )
            row = cur.fetchone()
            if not row:
                return None
            if not _verify_password(password, row["password_hash"]):
                return None
            return {
                "email": row["email"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "is_admin": bool(row["is_admin"]),
            }
        finally:
            conn.close()


def create_user_record(
    *,
    email: str,
    first_name: str,
    last_name: str,
) -> tuple[str, str] | None:
    """Returns (email, temporary_password) or None if email already exists."""
    key = email.strip().lower()
    fn = first_name.strip()
    ln = last_name.strip()
    if not key or not fn or not ln:
        raise ValueError("email, first_name, and last_name are required")
    temp_pw = secrets.token_urlsafe(14)

    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("SELECT id FROM users WHERE email = ?", (key,))
            if cur.fetchone():
                return None
            conn.execute(
                """
                INSERT INTO users (email, password_hash, first_name, last_name, is_admin)
                VALUES (?, ?, ?, ?, 0)
                """,
                (key, _hash_password(temp_pw), fn, ln),
            )
            conn.commit()
        finally:
            conn.close()
    return key, temp_pw
