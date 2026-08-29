"""Core modules: Configuration, Database, and Security foundations."""

from app.core.config import settings
from app.core.database import Base, get_db, init_db, engine, SessionLocal
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    oauth2_scheme
)

__all__ = [
    "settings",
    "Base",
    "get_db",
    "init_db",
    "engine",
    "SessionLocal",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "oauth2_scheme"
]
