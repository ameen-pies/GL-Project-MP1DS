"""Analytics and prediction payloads."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import UtcDateTime


class DayCount(BaseModel):
    date: str
    completed: int
    stopped: int


class WeeklyMissions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_date: str = Field(alias="from", serialization_alias="from")
    to_date: str = Field(alias="to", serialization_alias="to")
    days: list[DayCount]


class RiskSlot(BaseModel):
    ts: UtcDateTime
    probability: float
    level: str


class RiskForecast(BaseModel):
    refreshed_at: UtcDateTime
    threshold: float
    slots: list[RiskSlot]
