"""Telemetry payloads."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from app.models.common import as_utc

TelemetryStatusInput = Literal["active", "idle"]


class TelemetryIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    battery_pct: float = Field(ge=0, le=100)
    status: TelemetryStatusInput
    ts: datetime | None = None

    @field_validator("ts")
    @classmethod
    def _aware(cls, value: datetime | None) -> datetime | None:
        return as_utc(value)


class TelemetryAck(BaseModel):
    ok: bool = True
