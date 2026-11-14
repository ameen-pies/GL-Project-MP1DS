from app.models.alert import Alert
from app.models.enums import AlertType
from app.models.user import User
from app.services.alerts import create_alert, notify_company


def _raise(client, seed, type_="intrusion"):
    return client.post(
        "/api/v1/robot/events",
        json={"type": type_, "lat": 35.8256, "lng": 10.6369},
        headers=seed["robot_headers"],
    )


def test_robot_event_creates_alert_for_its_company(client, seed, db):
    response = _raise(client, seed, "intrusion")
    assert response.status_code == 201
    alert_id = response.json()["id"]

    alert = db.get(Alert, alert_id)
    assert alert.company_id == seed["demo"].id
    assert alert.type is AlertType.INTRUSION

    listed = client.get("/api/v1/alerts", headers=seed["operator_headers"]).json()
    assert len(listed) == 1
    assert listed[0]["robot_name"] == "Atlas"
    assert listed[0]["acknowledged"] is False

    other = client.get("/api/v1/alerts", headers=seed["other_admin_headers"]).json()
    assert other == []


def test_invalid_type_and_key_are_rejected(client, seed):
    assert _raise(client, seed, "fire").status_code == 422
    response = client.post(
        "/api/v1/robot/events",
        json={"type": "intrusion", "lat": 0, "lng": 0},
        headers={"X-Robot-Key": "nope"},
    )
    assert response.status_code == 401


def test_acknowledge_records_who_and_when(client, seed, db):
    alert_id = _raise(client, seed).json()["id"]
    response = client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge", headers=seed["operator_headers"]
    )
    assert response.status_code == 200
    body = response.json()
    assert body["acknowledged"] is True
    assert body["acknowledged_by"] == seed["operator"].id
    assert body["acknowledged_by_name"] == "Youssef Trabelsi"
    assert body["acknowledged_at"] is not None

    again = client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge", headers=seed["operator_headers"]
    )
    assert again.status_code == 200
    assert again.json()["acknowledged_by"] == seed["operator"].id

    assert client.get("/api/v1/alerts", headers=seed["operator_headers"]).json() == []
    assert len(client.get("/api/v1/alerts?status=all", headers=seed["operator_headers"]).json()) == 1


def test_other_company_alert_is_not_found(client, seed):
    alert_id = _raise(client, seed).json()["id"]
    response = client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge", headers=seed["other_admin_headers"]
    )
    assert response.status_code == 404


def test_open_count_ignores_acknowledged_and_other_companies(client, seed):
    first = _raise(client, seed).json()["id"]
    _raise(client, seed, "obstacle")

    assert client.get("/api/v1/alerts/open-count", headers=seed["operator_headers"]).json() == {
        "count": 2
    }
    client.post(f"/api/v1/alerts/{first}/acknowledge", headers=seed["operator_headers"])
    assert client.get("/api/v1/alerts/open-count", headers=seed["operator_headers"]).json() == {
        "count": 1
    }
    assert client.get("/api/v1/alerts/open-count", headers=seed["other_admin_headers"]).json() == {
        "count": 0
    }


def test_notification_targets_opted_in_users_and_never_raises(client, seed, db, monkeypatch):
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "app.services.alerts.send_email",
        lambda to, subject, body: sent.append((to, subject)) or True,
    )

    seed["operator"].email_notifications = False
    db.commit()

    alert = create_alert(db, seed["robot"], AlertType.OBSTACLE, 35.8, 10.6)
    notify_company(db, alert)

    assert [recipient for recipient, _ in sent] == ["admin@demo.tn"]
    assert "obstacle alert from Atlas" in sent[0][1]

    def failing(*_args, **_kwargs):
        raise RuntimeError("smtp down")

    monkeypatch.setattr("app.services.alerts.send_email", failing)
    notify_company(db, alert)  # must not raise
