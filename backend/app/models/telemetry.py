"""Telemetry: one position, battery and status sample from a robot."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import utcnow
from app.models.enums import TelemetryStatus

if TYPE_CHECKING:
    from app.models.robot import Robot


class Telemetry(Base):
    __tablename__ = "telemetry"
    __table_args__ = (
        CheckConstraint("battery_pct >= 0 AND battery_pct <= 100", name="battery_range"),
        Index("ix_telemetry_robot_ts", "robot_id", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    robot_id: Mapped[int] = mapped_column(
        ForeignKey("robots.id", ondelete="CASCADE"),
        nullable=False,
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    battery_pct: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[TelemetryStatus] = mapped_column(
        SAEnum(
            TelemetryStatus,
            name="telemetry_status",
            native_enum=False,
            length=16,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )

    robot: Mapped["Robot"] = relationship(back_populates="telemetry")

    def __repr__(self) -> str:
        return f"<Telemetry robot={self.robot_id} ts={self.ts.isoformat()}>"
