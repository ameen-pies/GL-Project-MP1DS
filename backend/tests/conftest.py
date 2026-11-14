"""Test fixtures: a fresh in-memory database per test and a TestClient."""

import secrets
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers every model)
from app.core.security import create_access_token, hash_password, hash_robot_key
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.company import Company
from app.models.robot import Robot
from app.models.user import User, UserRole


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def client(db, monkeypatch):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    # Background alert notifications open their own session; point them at the
    # test database instead of the real file.
    import app.services.alerts as alerts_module

    monkeypatch.setattr(alerts_module, "SessionLocal", sessionmaker(bind=db.bind, expire_on_commit=False))

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def seed(db):
    demo = Company(name="Demo Security SA")
    other = Company(name="Other Site Security")
    db.add_all([demo, other])
    db.flush()

    admin = User(
        company_id=demo.id,
        email="admin@demo.tn",
        password_hash=hash_password("Admin123!"),
        full_name="Amina Ben Salah",
        role=UserRole.ADMIN,
    )
    operator = User(
        company_id=demo.id,
        email="operator@demo.tn",
        password_hash=hash_password("Operator123!"),
        full_name="Youssef Trabelsi",
        role=UserRole.OPERATOR,
    )
    other_admin = User(
        company_id=other.id,
        email="admin@other.tn",
        password_hash=hash_password("Admin123!"),
        full_name="Other Site Admin",
        role=UserRole.ADMIN,
    )
    db.add_all([admin, operator, other_admin])
    db.flush()

    robot = Robot(
        company_id=demo.id,
        name="Atlas",
        serial_number="ATLAS-001",
        api_key_hash=hash_robot_key("atlas-key"),
        api_key_prefix="atlas-ke",
    )
    other_robot = Robot(
        company_id=other.id,
        name="Other Unit",
        serial_number="OTHER-001",
        api_key_hash=hash_robot_key("other-key"),
        api_key_prefix="other-ke",
    )
    db.add_all([robot, other_robot])
    db.commit()

    return {
        "demo": demo,
        "other": other,
        "admin": admin,
        "operator": operator,
        "other_admin": other_admin,
        "robot": robot,
        "other_robot": other_robot,
        "admin_headers": _headers(admin),
        "operator_headers": _headers(operator),
        "other_admin_headers": _headers(other_admin),
        "robot_headers": {"X-Robot-Key": "atlas-key"},
        "other_robot_headers": {"X-Robot-Key": "other-key"},
    }


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def make_route(db, company_id: int, name: str = "North perimeter"):
    from app.models.mission import Route, Waypoint

    route = Route(company_id=company_id, name=name)
    db.add(route)
    db.flush()
    for seq, (lat, lng) in enumerate(
        [(35.8276, 10.6349), (35.8282, 10.6372), (35.8270, 10.6390)],
        start=1,
    ):
        db.add(Waypoint(route_id=route.id, seq=seq, lat=lat, lng=lng))
    db.commit()
    return route


def add_telemetry(db, robot_id: int, ts: datetime | None = None, battery: float = 80.0, status: str = "active"):
    from app.models.enums import TelemetryStatus
    from app.models.telemetry import Telemetry

    row = Telemetry(
        robot_id=robot_id,
        ts=ts or datetime.now(timezone.utc),
        lat=35.8256,
        lng=10.6369,
        battery_pct=battery,
        status=TelemetryStatus(status),
    )
    db.add(row)
    db.commit()
    return row


def unique_serial() -> str:
    return f"TEST-{secrets.token_hex(3)}"
