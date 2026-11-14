"""Shared schema helpers."""

from datetime import datetime
from typing import Annotated

from pydantic import PlainSerializer

from app.models.common import as_utc


def iso_utc(value: datetime | None) -> str | None:
    """Serialize a datetime as an ISO-8601 UTC string with a ``Z`` suffix."""
    if value is None:
        return None
    return as_utc(value).isoformat().replace("+00:00", "Z")


UtcDateTime = Annotated[
    datetime,
    PlainSerializer(iso_utc, return_type=str),
]
