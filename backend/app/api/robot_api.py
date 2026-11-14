"""Machine-facing endpoints authenticated with X-Robot-Key."""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_robot
from app.db.session import get_db
from app.models.mission import Mission
from app.models.enums import MissionStatus
from app.models.robot import Robot
from app.schemas.alerts import AlertCreated, AlertEventIn
from app.schemas.telemetry import TelemetryAck, TelemetryIn
from app.services.alerts import create_alert, notify_alert
from app.services.telemetry_repo import insert_telemetry
from app.models.common import utcnow

router = APIRouter(tags=["robot"])


@router.post(
    "/robot/telemetry",
    response_model=TelemetryAck,
    status_code=status.HTTP_201_CREATED,
    summary="Receive a telemetry sample from a robot",
)
def post_telemetry(
    payload: TelemetryIn,
    robot: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db),
) -> TelemetryAck:
    insert_telemetry(
        db,
        robot_id=robot.id,
        ts=payload.ts or utcnow(),
        lat=payload.lat,
        lng=payload.lng,
        battery_pct=payload.battery_pct,
        status=payload.status,
    )
    return TelemetryAck()


@router.get("/robot/mission", summary="Return this robot's running mission")
def robot_mission(
    robot: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db),
) -> dict:
    mission = db.scalar(
        select(Mission).where(
            Mission.robot_id == robot.id,
            Mission.status == MissionStatus.RUNNING,
        )
    )
    if mission is None:
        return {"mission": None}

    route = mission.route
    return {
        "mission": {
            "id": mission.id,
            "route": {
                "id": route.id,
                "name": route.name,
                "waypoints": [
                    {"seq": point.seq, "lat": point.lat, "lng": point.lng}
                    for point in route.waypoints
                ],
            },
        }
    }


@router.post(
    "/robot/events",
    response_model=AlertCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Raise an intrusion or obstacle alert",
)
def post_event(
    payload: AlertEventIn,
    background: BackgroundTasks,
    robot: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db),
) -> AlertCreated:
    alert = create_alert(
        db,
        robot,
        payload.type,
        lat=payload.lat,
        lng=payload.lng,
        ts=payload.ts,
    )
    background.add_task(notify_alert, alert.id)
    return AlertCreated(id=alert.id)
