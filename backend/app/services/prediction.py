"""Incident risk service.

Loads the trained model and its metrics once, builds the same feature rows
used in training, and caches the forecast for an hour.
"""

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any

import joblib

from app.core.config import settings

FEATURES = ["hour_sin", "hour_cos", "dow", "is_weekend", "is_night"]
CACHE_MINUTES = 60

_cache: dict[str, Any] = {}


class ModelUnavailable(Exception):
    """The trained model file is missing or unreadable."""


def _load() -> tuple[Any, dict]:
    try:
        model = joblib.load(settings.model_file)
        metrics = json.loads(settings.metrics_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ModelUnavailable from exc
    return model, metrics


def build_features(start: datetime, hours: int) -> list[list[float]]:
    """Calendar features for the next ``hours`` full hours, in training order."""
    rows = []
    for offset in range(hours):
        ts = start + timedelta(hours=offset)
        hour = ts.hour
        dow = ts.weekday()  # 0 = Monday
        rows.append(
            [
                math.sin(2 * math.pi * hour / 24),
                math.cos(2 * math.pi * hour / 24),
                dow,
                1 if dow >= 5 else 0,
                1 if (hour >= 22 or hour < 6) else 0,
            ]
        )
    return rows


def next_full_hour(now: datetime | None = None) -> datetime:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def risk_forecast(hours: int = 24, now: datetime | None = None, force: bool = False) -> dict:
    """Return the cached forecast, recomputing it after an hour or a size change."""
    now = now or datetime.now(timezone.utc)
    cached = _cache.get("forecast")
    if (
        not force
        and cached
        and cached["hours"] == hours
        and now - cached["computed_at"] < timedelta(minutes=CACHE_MINUTES)
    ):
        return cached["payload"]

    model, metrics = _load()
    threshold = float(metrics.get("threshold", 0.5))
    start = next_full_hour(now)
    probabilities = model.predict_proba(build_features(start, hours))[:, 1]

    slots = []
    for offset, probability in enumerate(probabilities):
        value = float(probability)
        if value >= threshold:
            level = "high"
        elif value >= 0.7 * threshold:
            level = "medium"
        else:
            level = "low"
        slots.append(
            {
                "ts": (start + timedelta(hours=offset)).isoformat().replace("+00:00", "Z"),
                "probability": round(value, 4),
                "level": level,
            }
        )

    payload = {
        "refreshed_at": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "threshold": threshold,
        "slots": slots,
    }
    _cache["forecast"] = {"hours": hours, "computed_at": now, "payload": payload}
    return payload


def reset_cache() -> None:
    _cache.clear()
