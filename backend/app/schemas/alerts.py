"""Alert payloads."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

from app.models.common import as_utc
from app.models.enums import AlertType
from app.schemas.common import UtcDateTime


class AlertEventIn(BaseModel):
    type: AlertType
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    ts: datetime | None = None

    @field_validator("ts")
    @classmethod
    def _aware(cls, value: datetime | None) -> datetime | None:
        return as_utc(value)


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    robot_id: int
    robot_name: str
    type: AlertType
    lat: float
    lng: float
    ts: UtcDateTime
    acknowledged: bool
    acknowledged_by: int | None = None
    acknowledged_by_name: str | None = None
    acknowledged_at: UtcDateTime | None = None


class AlertCreated(BaseModel):
    id: int


class AlertCount(BaseModel):
    count: int


AlertFilter = Literal["open", "all"]
