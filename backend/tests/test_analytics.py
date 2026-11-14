from datetime import datetime, timedelta, timezone

from app.analytics.queries import battery_history, missions_per_day, uptime_pct
from app.models.enums import MissionStatus
from app.models.mission import Mission, Route
from tests.conftest import add_telemetry, make_route


def _mission(db, seed, ended_at, status=MissionStatus.COMPLETED):
    route = db.query(Route).first()
    mission = Mission(
        company_id=seed["demo"].id,
        robot_id=seed["robot"].id,
        route_id=route.id,
        status=status,
        scheduled_at=ended_at - timedelta(hours=1),
        started_at=ended_at - timedelta(minutes=40),
        ended_at=ended_at,
        created_by=seed["admin"].id,
    )
    db.add(mission)
    db.commit()
    return mission


def test_missions_per_day_zero_fills_seven_days(db, seed):
    make_route(db, seed["demo"].id)
    today = datetime.now(timezone.utc).date()
    _mission(db, seed, datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=10))
    _mission(
        db,
        seed,
        datetime.combine(today - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=10),
        MissionStatus.STOPPED,
    )

    days = missions_per_day(db, seed["demo"].id, days=7, end_date=today)
    assert len(days) == 7
    assert days[-1] == {"date": today.isoformat(), "completed": 1, "stopped": 0}
    assert days[-2] == {
        "date": (today - timedelta(days=1)).isoformat(),
        "completed": 0,
        "stopped": 1,
    }
    assert days[0]["completed"] == 0


def test_missions_per_day_is_company_scoped(db, seed):
    make_route(db, seed["demo"].id)
    now = datetime.now(timezone.utc)
    route_id = db.query(Route).first().id
    other = Mission(
        company_id=seed["other"].id,
        robot_id=seed["other_robot"].id,
        route_id=route_id,
        status=MissionStatus.COMPLETED,
        scheduled_at=now,
        ended_at=now,
        created_by=seed["other_admin"].id,
    )
    db.add(other)
    db.commit()

    days = missions_per_day(db, seed["demo"].id, days=7)
    assert sum(day["completed"] for day in days) == 0


def test_weekly_endpoint(client, seed, db):
    make_route(db, seed["demo"].id)
    now = datetime.now(timezone.utc)
    _mission(db, seed, now)

    response = client.get("/api/v1/analytics/missions/weekly", headers=seed["operator_headers"])
    assert response.status_code == 200
    body = response.json()
    assert body["from"] <= body["to"]
    assert len(body["days"]) == 7
    assert body["days"][-1]["completed"] == 1

    previous = client.get(
        "/api/v1/analytics/missions/weekly?week_offset=1", headers=seed["operator_headers"]
    )
    assert previous.status_code == 200
    assert previous.json()["to"] < body["from"]

    assert client.get(
        "/api/v1/analytics/missions/weekly?week_offset=-1", headers=seed["operator_headers"]
    ).status_code == 422


def test_uptime_and_battery_history(db, seed):
    now = datetime.now(timezone.utc)
    for minute in range(5):
        add_telemetry(db, seed["robot"].id, ts=now - timedelta(minutes=minute), battery=50 + minute)

    history = battery_history(db, seed["robot"].id, hours=24, bucket_minutes=10, now=now)
    assert history
    assert all(0 <= point["avg_battery"] <= 100 for point in history)

    assert 0 < uptime_pct(db, seed["robot"].id, days=1, now=now) < 1
    assert uptime_pct(db, seed["other_robot"].id, days=1, now=now) == 0
