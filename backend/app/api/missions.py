"""Routes and patrol missions."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.common import as_utc, utcnow
from app.models.enums import MissionStatus
from app.models.mission import Mission, MissionEvent, Route
from app.models.robot import Robot
from app.models.user import User
from app.schemas.missions import MissionCreate, MissionEventOut, MissionOut, RouteOut
from app.services.missions import MissionStateError, start_mission, stop_mission

router = APIRouter(tags=["missions"])


@router.get("/routes", response_model=list[RouteOut], summary="Company routes with waypoints")
def list_routes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Route]:
    return db.scalars(
        select(Route).where(Route.company_id == user.company_id).order_by(Route.name)
    ).all()


def _mission_out(mission: Mission) -> MissionOut:
    return MissionOut(
        id=mission.id,
        robot_id=mission.robot_id,
        robot_name=mission.robot.name,
        route_id=mission.route_id,
        route_name=mission.route.name,
        status=mission.status,
        scheduled_at=mission.scheduled_at,
        started_at=mission.started_at,
        ended_at=mission.ended_at,
        created_by=mission.created_by,
        events=[
            MissionEventOut(
                id=event.id,
                action=event.action,
                user_id=event.user_id,
                user_name=event.user.full_name if event.user else None,
                ts=event.ts,
            )
            for event in sorted(mission.events, key=lambda item: as_utc(item.ts))
        ],
    )


@router.post(
    "/missions",
    response_model=MissionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a mission on a seeded route",
)
def create_mission(
    payload: MissionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MissionOut:
    robot = db.scalar(
        select(Robot).where(
            Robot.id == payload.robot_id,
            Robot.company_id == user.company_id,
        )
    )
    route = db.scalar(
        select(Route).where(
            Route.id == payload.route_id,
            Route.company_id == user.company_id,
        )
    )
    if robot is None or route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Robot or route not found")

    mission = Mission(
        company_id=user.company_id,
        robot_id=robot.id,
        route_id=route.id,
        status=MissionStatus.SCHEDULED,
        scheduled_at=utcnow(),
        created_by=user.id,
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return _mission_out(mission)


@router.get("/missions", response_model=list[MissionOut], summary="Company missions, newest first")
def list_missions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MissionOut]:
    missions = db.scalars(
        select(Mission)
        .where(Mission.company_id == user.company_id)
        .order_by(Mission.created_at.desc(), Mission.id.desc())
    ).all()
    return [_mission_out(mission) for mission in missions]


def _get_mission(db: Session, mission_id: int, user: User) -> Mission:
    mission = db.scalar(
        select(Mission).where(
            Mission.id == mission_id,
            Mission.company_id == user.company_id,
        )
    )
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return mission


@router.post("/missions/{mission_id}/start", response_model=MissionOut)
def start(
    mission_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MissionOut:
    mission = _get_mission(db, mission_id, user)
    try:
        start_mission(db, mission, user.id)
    except MissionStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    return _mission_out(mission)


@router.post("/missions/{mission_id}/stop", response_model=MissionOut)
def stop(
    mission_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MissionOut:
    mission = _get_mission(db, mission_id, user)
    try:
        stop_mission(db, mission, user.id)
    except MissionStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    return _mission_out(mission)
