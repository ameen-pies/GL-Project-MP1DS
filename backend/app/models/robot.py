"""Robot: one patrol unit registered to a company."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import utcnow

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.company import Company
    from app.models.mission import Mission
    from app.models.telemetry import Telemetry


class Robot(Base):
    __tablename__ = "robots"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    serial_number: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        index=True,
        nullable=False,
    )
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_prefix: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="robots")
    telemetry: Mapped[list["Telemetry"]] = relationship(
        back_populates="robot",
        cascade="all, delete-orphan",
    )
    missions: Mapped[list["Mission"]] = relationship(back_populates="robot")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="robot")

    def __repr__(self) -> str:
        return f"<Robot id={self.id} serial={self.serial_number!r}>"
