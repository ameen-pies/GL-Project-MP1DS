"""Alert queue for operators."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.alert import Alert
from app.models.common import utcnow
from app.models.user import User
from app.schemas.alerts import AlertCount, AlertFilter, AlertOut

router = APIRouter(tags=["alerts"])


def _alert_out(alert: Alert) -> AlertOut:
    return AlertOut(
        id=alert.id,
        robot_id=alert.robot_id,
        robot_name=alert.robot.name,
        type=alert.type,
        lat=alert.lat,
        lng=alert.lng,
        ts=alert.ts,
        acknowledged=alert.acknowledged,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_by_name=alert.acknowledger.full_name if alert.acknowledger else None,
        acknowledged_at=alert.acknowledged_at,
    )


@router.get("/alerts", response_model=list[AlertOut], summary="Alert queue")
def list_alerts(
    alert_status: AlertFilter = Query(default="open", alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AlertOut]:
    query = select(Alert).where(Alert.company_id == user.company_id)
    if alert_status == "open":
        query = query.where(Alert.acknowledged.is_(False))
    alerts = db.scalars(query.order_by(Alert.ts.desc(), Alert.id.desc())).all()
    return [_alert_out(alert) for alert in alerts]


@router.get("/alerts/open-count", response_model=AlertCount, summary="Open alert count")
def open_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertCount:
    count = db.scalar(
        select(func.count(Alert.id)).where(
            Alert.company_id == user.company_id,
            Alert.acknowledged.is_(False),
        )
    )
    return AlertCount(count=int(count or 0))


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge(
    alert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertOut:
    alert = db.scalar(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.company_id == user.company_id,
        )
    )
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if not alert.acknowledged:
        alert.acknowledged = True
        alert.acknowledged_by = user.id
        alert.acknowledged_at = utcnow()
        db.commit()
        db.refresh(alert)
    return _alert_out(alert)
