from sqlalchemy import func, select

from app.models.telemetry import Telemetry
from app.services.telemetry_repo import get_latest, get_latest_for_company
from tests.conftest import add_telemetry
from datetime import datetime, timedelta, timezone


def test_robot_can_post_telemetry(client, seed, db):
    response = client.post(
        "/api/v1/robot/telemetry",
        json={"lat": 35.82, "lng": 10.63, "battery_pct": 87.5, "status": "active"},
        headers=seed["robot_headers"],
    )
    assert response.status_code == 201
    assert response.json() == {"ok": True}

    row = db.scalar(select(Telemetry))
    assert row is not None
    assert row.robot_id == seed["robot"].id
    assert row.battery_pct == 87.5


def test_unknown_or_missing_key_is_rejected(client, seed):
    payload = {"lat": 35.82, "lng": 10.63, "battery_pct": 50, "status": "idle"}
    assert client.post("/api/v1/robot/telemetry", json=payload).status_code == 401
    response = client.post(
        "/api/v1/robot/telemetry",
        json=payload,
        headers={"X-Robot-Key": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid robot key"


def test_invalid_telemetry_is_422(client, seed):
    for payload in (
        {"lat": 35.82, "lng": 10.63, "battery_pct": 150, "status": "active"},
        {"lng": 10.63, "battery_pct": 50, "status": "active"},
        {"lat": 120, "lng": 10.63, "battery_pct": 50, "status": "active"},
        {"lat": 35.82, "lng": 10.63, "battery_pct": 50, "status": "flying"},
    ):
        response = client.post(
            "/api/v1/robot/telemetry", json=payload, headers=seed["robot_headers"]
        )
        assert response.status_code == 422


def test_robots_do_not_mix(client, seed, db):
    client.post(
        "/api/v1/robot/telemetry",
        json={"lat": 35.82, "lng": 10.63, "battery_pct": 80, "status": "active"},
        headers=seed["robot_headers"],
    )
    client.post(
        "/api/v1/robot/telemetry",
        json={"lat": 36.0, "lng": 10.0, "battery_pct": 40, "status": "idle"},
        headers=seed["other_robot_headers"],
    )
    demo = client.get("/api/v1/robots/latest", headers=seed["operator_headers"]).json()
    other = client.get("/api/v1/robots/latest", headers=seed["other_admin_headers"]).json()
    assert demo[0]["lat"] == 35.82
    assert other[0]["lat"] == 36.0


def test_repo_returns_latest_rows(seed, db):
    now = datetime.now(timezone.utc)
    add_telemetry(db, seed["robot"].id, ts=now - timedelta(minutes=5), battery=70)
    newest = add_telemetry(db, seed["robot"].id, ts=now, battery=60)

    assert get_latest(db, seed["robot"].id).id == newest.id
    latest = get_latest_for_company(db, seed["demo"].id)
    assert latest[seed["robot"].id].battery_pct == 60

    total = db.scalar(select(func.count(Telemetry.id)))
    assert total == 2
