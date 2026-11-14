"""Company: the tenant boundary for every query."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import utcnow

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.mission import Mission, Route
    from app.models.robot import Robot
    from app.models.user import User


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    robots: Mapped[list["Robot"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    routes: Mapped[list["Route"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    missions: Mapped[list["Mission"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r}>"
