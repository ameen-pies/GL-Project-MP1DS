"""Data access for telemetry.

Plain functions: no HTTP, no request objects. The API layer and the scripts
share them.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.common import as_utc
from app.models.enums import TelemetryStatus
from app.models.robot import Robot
from app.models.telemetry import Telemetry


def insert_telemetry(
    db: Session,
    robot_id: int,
    ts: datetime,
    lat: float,
    lng: float,
    battery_pct: float,
    status: TelemetryStatus | str,
) -> Telemetry:
    row = Telemetry(
        robot_id=robot_id,
        ts=as_utc(ts),
        lat=lat,
        lng=lng,
        battery_pct=battery_pct,
        status=TelemetryStatus(status),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_latest(db: Session, robot_id: int) -> Telemetry | None:
    return db.scalar(
        select(Telemetry)
        .where(Telemetry.robot_id == robot_id)
        .order_by(Telemetry.ts.desc(), Telemetry.id.desc())
        .limit(1)
    )


def get_latest_for_company(db: Session, company_id: int) -> dict[int, Telemetry]:
    """Return the newest telemetry row per robot for one company.

    ``SELECT DISTINCT ON`` is PostgreSQL-only, so this uses a window function
    (supported by both SQLite and PostgreSQL).
    """
    ranked = (
        select(
            Telemetry.id.label("id"),
            func.row_number()
            .over(
                partition_by=Telemetry.robot_id,
                order_by=(Telemetry.ts.desc(), Telemetry.id.desc()),
            )
            .label("rank"),
        )
        .join(Robot, Robot.id == Telemetry.robot_id)
        .where(Robot.company_id == company_id)
        .subquery()
    )

    rows = db.scalars(
        select(Telemetry).where(
            Telemetry.id.in_(select(ranked.c.id).where(ranked.c.rank == 1))
        )
    ).all()
    return {row.robot_id: row for row in rows}
