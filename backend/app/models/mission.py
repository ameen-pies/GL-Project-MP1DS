"""Routes, waypoints, missions and the mission event log."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import utcnow
from app.models.enums import MissionAction, MissionStatus

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.robot import Robot
    from app.models.user import User


def _enum(enum_class, name: str) -> SAEnum:
    return SAEnum(
        enum_class,
        name=name,
        native_enum=False,
        length=16,
        values_callable=lambda values: [value.value for value in values],
    )


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="routes")
    waypoints: Mapped[list["Waypoint"]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="Waypoint.seq",
    )
    missions: Mapped[list["Mission"]] = relationship(back_populates="route")

    def __repr__(self) -> str:
        return f"<Route id={self.id} name={self.name!r}>"


class Waypoint(Base):
    __tablename__ = "waypoints"
    __table_args__ = (UniqueConstraint("route_id", "seq", name="route_seq"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)

    route: Mapped["Route"] = relationship(back_populates="waypoints")

    def __repr__(self) -> str:
        return f"<Waypoint route={self.route_id} seq={self.seq}>"


class Mission(Base):
    __tablename__ = "missions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'running', 'completed', 'stopped', 'cancelled')",
            name="status_allowed",
        ),
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
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[MissionStatus] = mapped_column(
        _enum(MissionStatus, "mission_status"),
        default=MissionStatus.SCHEDULED,
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="missions")
    robot: Mapped["Robot"] = relationship(back_populates="missions")
    route: Mapped["Route"] = relationship(back_populates="missions")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    events: Mapped[list["MissionEvent"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="MissionEvent.ts",
    )

    def __repr__(self) -> str:
        return f"<Mission id={self.id} status={self.status.value}>"


class MissionEvent(Base):
    __tablename__ = "mission_events"
    __table_args__ = (
        CheckConstraint("action IN ('start', 'stop')", name="action_allowed"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(
        ForeignKey("missions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    action: Mapped[MissionAction] = mapped_column(
        _enum(MissionAction, "mission_action"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    mission: Mapped["Mission"] = relationship(back_populates="events")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<MissionEvent mission={self.mission_id} action={self.action.value}>"
