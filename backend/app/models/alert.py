"""Alerts raised by robots when they detect an intrusion or an obstacle."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import utcnow
from app.models.enums import AlertType

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.robot import Robot
    from app.models.user import User


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_company_ack_ts", "company_id", "acknowledged", "ts"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    robot_id: Mapped[int] = mapped_column(
        ForeignKey("robots.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[AlertType] = mapped_column(
        SAEnum(
            AlertType,
            name="alert_type",
            native_enum=False,
            length=16,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    acknowledged_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    company: Mapped["Company"] = relationship(back_populates="alerts")
    robot: Mapped["Robot"] = relationship(back_populates="alerts")
    acknowledger: Mapped["User | None"] = relationship(foreign_keys=[acknowledged_by])

    def __repr__(self) -> str:
        return f"<Alert id={self.id} type={self.type.value}>"
