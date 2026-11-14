"""Shared model helpers."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware timestamp used as a Python-side column default."""
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    """Return an aware UTC datetime.

    SQLite drops the timezone, so values read back from the database are
    naive. They were written as UTC, so attach it back before comparing.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
