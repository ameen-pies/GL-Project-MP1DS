"""Generate a week of realistic demo data.

Creates (if missing) five robots for the demo company, 7 days of telemetry at
one sample every 10 seconds, about 40 finished missions, and some alerts.

    python -m scripts.seed_demo_data --reset
"""

import argparse
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.core.security import hash_robot_key
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.company import Company
from app.models.enums import AlertType, MissionStatus, TelemetryStatus
from app.models.mission import Mission, MissionEvent, Route
from app.models.robot import Robot
from app.models.telemetry import Telemetry
from app.models.user import User, UserRole
from app.services.alerts import create_alert
from scripts.seed_routes import seed_routes
from scripts.seed_users import seed_users

SOUSSE = (35.8256, 10.6369)
ROBOT_NAMES = ["Atlas", "Bastion", "Cyclops", "Dune", "Echo"]


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _ensure_robots(db: Session, company: Company) -> list[Robot]:
    robots = db.scalars(
        select(Robot).where(Robot.company_id == company.id).order_by(Robot.id)
    ).all()
    for name in ROBOT_NAMES:
        if len(robots) >= 5:
            break
        if any(robot.name == name for robot in robots):
            continue
        robot = Robot(
            company_id=company.id,
            name=name,
            serial_number=f"SIM-{name.upper()}",
            api_key_hash=hash_robot_key(f"demo-{name.lower()}-key"),
            api_key_prefix=f"SIM-{name[:3].upper()}",
        )
        db.add(robot)
        robots.append(robot)
    db.commit()
    return robots[:5]


def _seed_telemetry(db: Session, robots: list[Robot], now: datetime) -> int:
    rows: list[dict] = []
    total = 0
    for robot_index, robot in enumerate(robots):
        battery = 92.0 - robot_index * 7
        lat = SOUSSE[0] + (robot_index - 2) * 0.0008
        lng = SOUSSE[1] + (robot_index - 2) * 0.0006
        for step in range(7 * 24 * 360):
            ts = now - timedelta(seconds=10 * (7 * 24 * 360 - step))
            hour = ts.hour
            active = 6 <= hour < 22
            battery = max(8.0, battery - (0.035 if active else 0.01))
            if step % 1440 == 0:
                battery = min(100.0, battery + 55)
            lat += random.uniform(-0.00008, 0.00008)
            lng += random.uniform(-0.00008, 0.00008)
            rows.append(
                {
                    "robot_id": robot.id,
                    "ts": ts.replace(tzinfo=None),
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "battery_pct": round(battery, 2),
                    "status": TelemetryStatus.ACTIVE if active else TelemetryStatus.IDLE,
                    "received_at": ts.replace(tzinfo=None),
                }
            )
            if len(rows) >= 5000:
                db.execute(insert(Telemetry), rows)
                total += len(rows)
                rows = []
    if rows:
        db.execute(insert(Telemetry), rows)
        total += len(rows)
    db.commit()
    return total


def _seed_missions(db: Session, company: Company, robots: list[Robot], admin: User, now: datetime) -> int:
    routes = db.scalars(select(Route).where(Route.company_id == company.id)).all()
    if not routes:
        return 0

    created = 0
    for day in range(6, -1, -1):
        for _ in range(random.randint(4, 7)):
            robot = random.choice(robots)
            route = random.choice(routes)
            started = (now - timedelta(days=day)).replace(hour=random.randint(6, 21), minute=0, second=0)
            duration = timedelta(minutes=random.randint(25, 70))
            completed = random.random() < 0.75
            mission = Mission(
                company_id=company.id,
                robot_id=robot.id,
                route_id=route.id,
                status=MissionStatus.COMPLETED if completed else MissionStatus.STOPPED,
                scheduled_at=started - timedelta(minutes=5),
                started_at=started,
                ended_at=started + duration,
                created_by=admin.id,
            )
            db.add(mission)
            db.flush()
            db.add(
                MissionEvent(
                    mission_id=mission.id,
                    action="start",
                    user_id=admin.id,
                    ts=started,
                )
            )
            db.add(
                MissionEvent(
                    mission_id=mission.id,
                    action="stop",
                    user_id=admin.id,
                    ts=started + duration,
                )
            )
            created += 1
    db.commit()
    return created


def reset_demo_data(db: Session, company_id: int) -> None:
    db.execute(delete(Alert).where(Alert.company_id == company_id))
    db.execute(delete(MissionEvent).where(MissionEvent.mission_id.in_(
        select(Mission.id).where(Mission.company_id == company_id)
    )))
    db.execute(delete(Mission).where(Mission.company_id == company_id))
    db.execute(delete(Telemetry).where(Telemetry.robot_id.in_(
        select(Robot.id).where(Robot.company_id == company_id)
    )))
    db.commit()


def seed_demo_data(reset: bool = False) -> None:
    init_db()
    seed_users()
    seed_routes()

    db = SessionLocal()
    try:
        company = db.scalar(select(Company).where(Company.name == "Demo Security SA"))
        if company is None:
            raise SystemExit("Demo company is missing.")
        admin = db.scalar(
            select(User).where(User.company_id == company.id, User.role == UserRole.ADMIN)
        )
        if admin is None:
            raise SystemExit("Demo admin is missing.")

        if reset:
            reset_demo_data(db, company.id)
            print("Existing demo telemetry, missions and alerts removed.")

        robots = _ensure_robots(db, company)
        now = datetime.now(timezone.utc)
        count = _seed_telemetry(db, robots, now)
        print(f"Telemetry rows inserted: {count}")

        missions = _seed_missions(db, company, robots, admin, now)
        print(f"Missions inserted: {missions}")

        alert_types = [AlertType.OBSTACLE, AlertType.OBSTACLE, AlertType.INTRUSION]
        for _ in range(18):
            robot = random.choice(robots)
            ts = now - timedelta(hours=random.uniform(0, 7 * 24))
            create_alert(
                db,
                robot,
                random.choice(alert_types),
                lat=round(SOUSSE[0] + random.uniform(-0.003, 0.003), 6),
                lng=round(SOUSSE[1] + random.uniform(-0.003, 0.003), 6),
                ts=ts,
            )
        print("Alerts inserted: 18")
        print("Demo data ready. Run ml/export_incidents.py to build the incident dataset.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="delete existing demo telemetry/missions/alerts first")
    args = parser.parse_args()
    seed_demo_data(reset=args.reset)
