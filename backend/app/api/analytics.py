"""Weekly patrol statistics."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.queries import missions_per_day
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import DayCount, WeeklyMissions

router = APIRouter(tags=["analytics"])


@router.get("/analytics/missions/weekly", response_model=WeeklyMissions)
def weekly_missions(
    week_offset: int = Query(default=0, ge=0, le=52),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WeeklyMissions:
    today = datetime.now(timezone.utc).date()
    end = today - timedelta(days=7 * week_offset)
    days = missions_per_day(db, user.company_id, days=7, end_date=end)
    return WeeklyMissions(
        from_date=days[0]["date"],
        to_date=days[-1]["date"],
        days=[DayCount(**day) for day in days],
    )
