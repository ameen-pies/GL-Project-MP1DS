"""Robot payloads."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import UtcDateTime

SerialNumber = Annotated[
    str,
    Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_-]+$"),
]

RobotStatus = Literal["active", "idle", "offline"]


class RobotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    serial_number: SerialNumber


class RobotCreated(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    serial_number: str
    created_at: UtcDateTime
    api_key: str


class RobotOut(BaseModel):
    id: int
    name: str
    serial_number: str
    status: RobotStatus
    battery_pct: float | None = None
    last_seen: UtcDateTime | None = None


class RobotLatestOut(RobotOut):
    lat: float | None = None
    lng: float | None = None
