"""Incident risk forecast."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import RiskForecast, RiskSlot
from app.services.prediction import ModelUnavailable, risk_forecast

router = APIRouter(tags=["predictions"])


@router.get("/predictions/risk", response_model=RiskForecast)
def risk(
    hours: int = Query(default=24, ge=1, le=72),
    _: User = Depends(get_current_user),
) -> RiskForecast:
    try:
        forecast = risk_forecast(hours=hours)
    except ModelUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model not available. Run ml/train.py.",
        ) from None

    return RiskForecast(
        refreshed_at=forecast["refreshed_at"],
        threshold=forecast["threshold"],
        slots=[RiskSlot(**slot) for slot in forecast["slots"]],
    )
