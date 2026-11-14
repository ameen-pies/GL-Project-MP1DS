"""Robot status rule: a robot is offline once its last sample is a minute old."""

from datetime import datetime

from app.models.common import as_utc, utcnow
from app.models.telemetry import Telemetry

OFFLINE_AFTER_SECONDS = 60


def compute_status(
    latest_telemetry: Telemetry | None,
    now: datetime | None = None,
) -> str:
    """Return ``active``, ``idle`` or ``offline`` for the latest sample."""
    if latest_telemetry is None:
        return "offline"

    current = as_utc(now or utcnow())
    last_seen = as_utc(latest_telemetry.ts)
    if last_seen is None:
        return "offline"

    age = (current - last_seen).total_seconds()
    if age > OFFLINE_AFTER_SECONDS:
        return "offline"
    return latest_telemetry.status.value
