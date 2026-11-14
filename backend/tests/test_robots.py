from app.models.robot import Robot
from app.services.robot_status import compute_status
from tests.conftest import add_telemetry, unique_serial
from datetime import datetime, timedelta, timezone


def test_admin_registers_a_robot_and_sees_the_key_once(client, seed, db):
    serial = unique_serial()
    response = client.post(
        "/api/v1/robots",
        json={"name": "Bastion", "serial_number": serial},
        headers=seed["admin_headers"],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["api_key"]
    assert body["name"] == "Bastion"

    stored = db.get(Robot, body["id"])
    assert stored.api_key_hash != body["api_key"]
    assert len(stored.api_key_hash) == 64
    assert stored.company_id == seed["demo"].id


def test_duplicate_serial_is_a_conflict(client, seed):
    response = client.post(
        "/api/v1/robots",
        json={"name": "Copy", "serial_number": "ATLAS-001"},
        headers=seed["admin_headers"],
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "A robot with this serial number already exists"


def test_operator_cannot_register(client, seed):
    response = client.post(
        "/api/v1/robots",
        json={"name": "Nope", "serial_number": unique_serial()},
        headers=seed["operator_headers"],
    )
    assert response.status_code == 403


def test_invalid_serial_is_rejected(client, seed):
    response = client.post(
        "/api/v1/robots",
        json={"name": "Bad", "serial_number": "a b!"},
        headers=seed["admin_headers"],
    )
    assert response.status_code == 422


def test_robot_list_is_company_scoped_and_searchable(client, seed, db):
    response = client.get("/api/v1/robots", headers=seed["admin_headers"])
    assert response.status_code == 200
    names = [robot["name"] for robot in response.json()]
    assert names == ["Atlas"]

    response = client.get("/api/v1/robots?search=atl", headers=seed["admin_headers"])
    assert [robot["name"] for robot in response.json()] == ["Atlas"]

    response = client.get("/api/v1/robots?search=zzz", headers=seed["admin_headers"])
    assert response.json() == []


def test_robot_list_requires_login(client, seed):
    assert client.get("/api/v1/robots").status_code == 401


def test_status_and_battery_are_reported(client, seed, db):
    add_telemetry(db, seed["robot"].id, battery=19.5, status="active")
    body = client.get("/api/v1/robots", headers=seed["operator_headers"]).json()
    assert body[0]["status"] == "active"
    assert body[0]["battery_pct"] == 19.5
    assert body[0]["last_seen"] is not None


def test_status_offline_after_sixty_seconds(client, seed, db):
    now = datetime.now(timezone.utc)
    add_telemetry(db, seed["robot"].id, ts=now - timedelta(seconds=61))
    body = client.get("/api/v1/robots/latest", headers=seed["operator_headers"]).json()
    assert body[0]["status"] == "offline"

    add_telemetry(db, seed["robot"].id, ts=now - timedelta(seconds=59))
    body = client.get("/api/v1/robots/latest", headers=seed["operator_headers"]).json()
    assert body[0]["status"] == "active"


def test_compute_status_edges(seed, db):
    now = datetime.now(timezone.utc)
    telemetry = add_telemetry(db, seed["robot"].id, ts=now - timedelta(seconds=60))
    assert compute_status(telemetry, now) == "active"
    assert compute_status(None, now) == "offline"


def test_latest_positions_are_company_scoped(client, seed, db):
    add_telemetry(db, seed["robot"].id)
    body = client.get("/api/v1/robots/latest", headers=seed["operator_headers"]).json()
    assert len(body) == 1
    assert body[0]["name"] == "Atlas"
    assert body[0]["lat"] == 35.8256

    body = client.get("/api/v1/robots/latest", headers=seed["other_admin_headers"]).json()
    assert [robot["name"] for robot in body] == ["Other Unit"]
    assert body[0]["lat"] is None
