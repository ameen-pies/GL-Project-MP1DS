import json
from datetime import datetime, timedelta, timezone

import joblib
import numpy as np
import pytest

from app.core.config import settings
from app.services import prediction


class FakeModel:
    def predict_proba(self, rows):
        values = np.array([0.05, 0.9, 0.25, 0.1] * 18)[: len(rows)]
        return np.column_stack([1 - values, values])


@pytest.fixture()
def fake_model(tmp_path, monkeypatch):
    model_file = tmp_path / "incident_model.joblib"
    metrics_file = tmp_path / "metrics.json"
    joblib.dump(FakeModel(), model_file)
    metrics_file.write_text(json.dumps({"threshold": 0.3}), encoding="utf-8")
    monkeypatch.setattr(settings, "model_path", str(model_file))
    prediction.reset_cache()
    yield {"threshold": 0.3}
    prediction.reset_cache()


def test_risk_returns_hours_starting_next_full_hour(client, seed, fake_model):
    now = datetime.now(timezone.utc)
    response = client.get("/api/v1/predictions/risk", headers=seed["operator_headers"])
    assert response.status_code == 200
    body = response.json()
    assert len(body["slots"]) == 24
    assert body["threshold"] == 0.3

    first = datetime.fromisoformat(body["slots"][0]["ts"].replace("Z", "+00:00"))
    expected = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    assert abs((first - expected).total_seconds()) < 5

    timestamps = [slot["ts"] for slot in body["slots"]]
    assert timestamps == sorted(timestamps)
    assert {slot["level"] for slot in body["slots"]} == {"low", "medium", "high"}


def test_hours_validation(client, seed, fake_model):
    assert client.get(
        "/api/v1/predictions/risk?hours=100", headers=seed["operator_headers"]
    ).status_code == 422
    assert client.get(
        "/api/v1/predictions/risk?hours=0", headers=seed["operator_headers"]
    ).status_code == 422


def test_forecast_is_cached(client, seed, fake_model):
    first = client.get("/api/v1/predictions/risk", headers=seed["operator_headers"]).json()
    second = client.get("/api/v1/predictions/risk", headers=seed["operator_headers"]).json()
    assert first["refreshed_at"] == second["refreshed_at"]


def test_missing_model_is_503(client, seed, tmp_path, monkeypatch):
    prediction.reset_cache()
    monkeypatch.setattr(settings, "model_path", str(tmp_path / "missing.joblib"))
    response = client.get("/api/v1/predictions/risk", headers=seed["operator_headers"])
    assert response.status_code == 503
    assert "Run ml/train.py" in response.json()["detail"]
    prediction.reset_cache()


def test_levels_follow_the_threshold():
    assert prediction.build_features(
        datetime(2026, 12, 30, 22, tzinfo=timezone.utc), 1
    )[0][4] == 1
