"""Alert creation and best-effort notification."""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alert
from app.models.common import as_utc, utcnow
from app.models.enums import AlertType
from app.models.robot import Robot
from app.models.user import User
from app.db.session import SessionLocal
from app.services.email import send_email

logger = logging.getLogger(__name__)


def create_alert(
    db: Session,
    robot: Robot,
    type_: AlertType,
    lat: float,
    lng: float,
    ts: datetime | None = None,
) -> Alert:
    alert = Alert(
        company_id=robot.company_id,
        robot_id=robot.id,
        type=AlertType(type_),
        lat=lat,
        lng=lng,
        ts=as_utc(ts) if ts else utcnow(),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def notify_company(db: Session, alert: Alert) -> None:
    """Email every opted-in user of the company. Failures are logged, not raised."""
    robot = db.get(Robot, alert.robot_id)
    robot_name = robot.name if robot else "a robot"
    recipients = db.scalars(
        select(User).where(
            User.company_id == alert.company_id,
            User.email_notifications.is_(True),
        )
    ).all()

    subject = f"[Fleet Control] {alert.type.value} alert from {robot_name}"
    body = (
        f"Robot: {robot_name}\n"
        f"Type: {alert.type.value}\n"
        f"Time: {as_utc(alert.ts).isoformat()}\n"
        f"Location: {alert.lat:.6f}, {alert.lng:.6f}\n\n"
        f"Open the queue: {settings.frontend_url}/alerts.html"
    )
    for user in recipients:
        try:
            send_email(user.email, subject, body)
        except Exception:
            # send_email already swallows its own failures; keep the caller safe
            # even if the mail transport is replaced or misbehaves.
            logger.exception("Alert notification failed for %s", user.email)


def notify_alert(alert_id: int) -> None:
    """Background task entry point: open a fresh session, then notify."""
    with SessionLocal() as db:
        alert = db.get(Alert, alert_id)
        if alert is not None:
            notify_company(db, alert)
