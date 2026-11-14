"""Statistics queries.

Functions take a session and return plain Python data. They never touch HTTP
objects, so they can be tested and reused by the ML scripts.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.common import as_utc, utcnow
from app.models.enums import MissionStatus
from app.models.mission import Mission
from app.models.telemetry import Telemetry


def missions_per_day(
    db: Session,
    company_id: int,
    days: int = 7,
    end_date: date | None = None,
) -> list[dict]:
    """Completed and stopped missions per day, zero-filled, oldest first."""
    end = end_date or datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)

    rows = db.execute(
        select(
            func.date(Mission.ended_at).label("day"),
            Mission.status,
            func.count().label("total"),
        )
        .where(
            Mission.company_id == company_id,
            Mission.ended_at.is_not(None),
            Mission.status.in_([MissionStatus.COMPLETED, MissionStatus.STOPPED]),
            func.date(Mission.ended_at) >= start.isoformat(),
            func.date(Mission.ended_at) <= end.isoformat(),
        )
        .group_by(func.date(Mission.ended_at), Mission.status)
    ).all()

    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"completed": 0, "stopped": 0})
    for day, status, total in rows:
        buckets[str(day)][status.value] = int(total)

    result = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).isoformat()
        counts = buckets.get(day, {"completed": 0, "stopped": 0})
        result.append(
            {
                "date": day,
                "completed": counts.get("completed", 0),
                "stopped": counts.get("stopped", 0),
            }
        )
    return result


def battery_history(
    db: Session,
    robot_id: int,
    hours: int = 24,
    bucket_minutes: int = 10,
    now: datetime | None = None,
) -> list[dict]:
    """Average battery percentage per time bucket."""
    end = as_utc(now) or utcnow()
    start = end - timedelta(hours=hours)
    bucket_seconds = max(1, bucket_minutes * 60)

    rows = db.execute(
        select(Telemetry.ts, Telemetry.battery_pct).where(
            Telemetry.robot_id == robot_id,
            Telemetry.ts >= start.replace(tzinfo=None),
            Telemetry.ts <= end.replace(tzinfo=None),
        )
    ).all()

    buckets: dict[int, list[float]] = defaultdict(list)
    for ts, battery in rows:
        moment = as_utc(ts).timestamp()
        buckets[int(moment // bucket_seconds) * bucket_seconds].append(float(battery))

    return [
        {
            "ts": datetime.fromtimestamp(key, tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "avg_battery": round(sum(values) / len(values), 2),
        }
        for key, values in sorted(buckets.items())
    ]


def uptime_pct(
    db: Session,
    robot_id: int,
    days: int = 7,
    now: datetime | None = None,
) -> float:
    """Percentage of one-minute buckets in the window that received telemetry."""
    end = as_utc(now) or utcnow()
    start = end - timedelta(days=days)

    timestamps = db.scalars(
        select(Telemetry.ts).where(
            Telemetry.robot_id == robot_id,
            Telemetry.ts >= start.replace(tzinfo=None),
            Telemetry.ts <= end.replace(tzinfo=None),
        )
    ).all()

    total_minutes = max(1, int((end - start).total_seconds() // 60))
    seen = {
        int(as_utc(ts).timestamp() // 60)
        for ts in timestamps
    }
    return round(min(100.0, len(seen) / total_minutes * 100), 1)
