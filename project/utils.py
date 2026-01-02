from __future__ import annotations
import uuid
from datetime import datetime, date
import hashlib
from typing import Any


def gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


def now() -> datetime:
    return datetime.utcnow()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def age_from_birthdate(bd: date) -> int:
    today = date.today()
    years = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    return years
