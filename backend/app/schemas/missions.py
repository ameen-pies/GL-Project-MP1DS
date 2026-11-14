"""Mission and route payloads."""

from pydantic import BaseModel, ConfigDict

from app.models.enums import MissionAction, MissionStatus
from app.schemas.common import UtcDateTime


class WaypointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq: int
    lat: float
    lng: float


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    waypoints: list[WaypointOut]


class MissionCreate(BaseModel):
    robot_id: int
    route_id: int


class MissionEventOut(BaseModel):
    id: int
    action: MissionAction
    user_id: int
    user_name: str | None = None
    ts: UtcDateTime


class MissionOut(BaseModel):
    id: int
    robot_id: int
    robot_name: str
    route_id: int
    route_name: str
    status: MissionStatus
    scheduled_at: UtcDateTime
    started_at: UtcDateTime | None
    ended_at: UtcDateTime | None
    created_by: int
    events: list[MissionEventOut] = []


class RobotMissionOut(BaseModel):
    id: int
    route: dict
