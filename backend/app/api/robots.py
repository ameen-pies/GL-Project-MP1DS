"""Robot registration, fleet list, and latest positions."""

import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.core.security import hash_robot_key
from app.db.session import get_db
from app.models.common import utcnow
from app.models.robot import Robot
from app.models.user import User
from app.schemas.robots import RobotCreate, RobotCreated, RobotLatestOut, RobotOut
from app.services.robot_status import compute_status
from app.services.telemetry_repo import get_latest_for_company

router = APIRouter(tags=["robots"])

DUPLICATE_SERIAL = "A robot with this serial number already exists"


@router.post(
    "/robots",
    response_model=RobotCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Register a robot and return its API key once",
)
def create_robot(
    payload: RobotCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RobotCreated:
    if db.scalar(select(Robot.id).where(Robot.serial_number == payload.serial_number)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_SERIAL)

    api_key = secrets.token_urlsafe(32)
    robot = Robot(
        company_id=admin.company_id,
        name=payload.name.strip(),
        serial_number=payload.serial_number,
        api_key_hash=hash_robot_key(api_key),
        api_key_prefix=api_key[:8],
    )
    db.add(robot)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_SERIAL) from None
    db.refresh(robot)

    return RobotCreated(
        id=robot.id,
        name=robot.name,
        serial_number=robot.serial_number,
        created_at=robot.created_at,
        api_key=api_key,
    )


@router.get("/robots", response_model=list[RobotOut], summary="List the company fleet")
def list_robots(
    search: str | None = Query(default=None, max_length=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RobotOut]:
    query = select(Robot).where(Robot.company_id == user.company_id)
    if search:
        query = query.where(Robot.name.ilike(f"%{search}%"))
    robots = db.scalars(query.order_by(Robot.name, Robot.id)).all()

    latest = get_latest_for_company(db, user.company_id)
    now = utcnow()
    return [
        RobotOut(
            id=robot.id,
            name=robot.name,
            serial_number=robot.serial_number,
            status=compute_status(latest.get(robot.id), now),
            battery_pct=_battery(latest.get(robot.id)),
            last_seen=_last_seen(latest.get(robot.id)),
        )
        for robot in robots
    ]


@router.get(
    "/robots/latest",
    response_model=list[RobotLatestOut],
    summary="Latest position and state per robot",
)
def latest_positions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RobotLatestOut]:
    robots = db.scalars(
        select(Robot).where(Robot.company_id == user.company_id).order_by(Robot.name, Robot.id)
    ).all()
    latest = get_latest_for_company(db, user.company_id)
    now = utcnow()

    return [
        RobotLatestOut(
            id=robot.id,
            name=robot.name,
            serial_number=robot.serial_number,
            status=compute_status(latest.get(robot.id), now),
            battery_pct=_battery(latest.get(robot.id)),
            last_seen=_last_seen(latest.get(robot.id)),
            lat=latest[robot.id].lat if robot.id in latest else None,
            lng=latest[robot.id].lng if robot.id in latest else None,
        )
        for robot in robots
    ]


def _battery(row) -> float | None:
    return row.battery_pct if row is not None else None


def _last_seen(row) -> datetime | None:
    return row.ts if row is not None else None
