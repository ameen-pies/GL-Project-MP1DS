"""Mission state machine.

Transitions are the only way mission status changes; the API maps
``MissionStateError`` to a 409.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.common import utcnow
from app.models.enums import MissionAction, MissionStatus
from app.models.mission import Mission, MissionEvent


class MissionStateError(Exception):
    """Raised when an action is not allowed from the mission's current state."""


def _event(db: Session, mission: Mission, action: MissionAction, user_id: int, ts: datetime) -> None:
    db.add(MissionEvent(mission_id=mission.id, action=action, user_id=user_id, ts=ts))


def start_mission(db: Session, mission: Mission, user_id: int, now: datetime | None = None) -> Mission:
    if mission.status is not MissionStatus.SCHEDULED:
        raise MissionStateError("This mission cannot be started")

    running = db.scalar(
        select(Mission).where(
            Mission.robot_id == mission.robot_id,
            Mission.status == MissionStatus.RUNNING,
            Mission.id != mission.id,
        )
    )
    if running is not None:
        raise MissionStateError("This robot already has a running mission")

    ts = utcnow() if now is None else now
    mission.status = MissionStatus.RUNNING
    mission.started_at = ts
    _event(db, mission, MissionAction.START, user_id, ts)
    db.commit()
    db.refresh(mission)
    return mission


def stop_mission(db: Session, mission: Mission, user_id: int, now: datetime | None = None) -> Mission:
    if mission.status is not MissionStatus.RUNNING:
        raise MissionStateError("This mission is not running")

    ts = utcnow() if now is None else now
    mission.status = MissionStatus.STOPPED
    mission.ended_at = ts
    _event(db, mission, MissionAction.STOP, user_id, ts)
    db.commit()
    db.refresh(mission)
    return mission
