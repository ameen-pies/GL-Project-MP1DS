"""Seed two patrol routes with waypoints around Sousse. Idempotent."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.mission import Route, Waypoint

SOUSSE = (35.8256, 10.6369)

ROUTES = {
    "North perimeter": [
        (35.8276, 10.6349),
        (35.8282, 10.6372),
        (35.8270, 10.6390),
        (35.8250, 10.6383),
        (35.8242, 10.6360),
        (35.8258, 10.6344),
    ],
    "Main gate loop": [
        (35.8248, 10.6352),
        (35.8262, 10.6361),
        (35.8268, 10.6378),
        (35.8255, 10.6388),
        (35.8238, 10.6374),
    ],
}


def seed_routes(db: Session | None = None) -> None:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        company = db.scalar(select(Company).where(Company.name == "Demo Security SA"))
        if company is None:
            raise SystemExit("Run scripts.seed_users first: demo company is missing.")

        for name, points in ROUTES.items():
            route = db.scalar(
                select(Route).where(Route.company_id == company.id, Route.name == name)
            )
            if route is None:
                route = Route(company_id=company.id, name=name)
                db.add(route)
                db.flush()
            existing = {point.seq for point in route.waypoints}
            for seq, (lat, lng) in enumerate(points, start=1):
                if seq not in existing:
                    db.add(Waypoint(route_id=route.id, seq=seq, lat=lat, lng=lng))
        db.commit()
        print(f"Routes ready for {company.name}: {', '.join(ROUTES)}")
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    init_db()
    seed_routes()
