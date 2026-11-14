"""Insert telemetry at 1 Hz for several robots and report insert latency.

    python -m scripts.telemetry_load_test --robots 5 --seconds 60
"""

import argparse
import secrets
import statistics
import threading
import time
from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.core.security import hash_robot_key
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.robot import Robot
from app.models.telemetry import Telemetry
from app.models.user import User
from app.services.telemetry_repo import insert_telemetry


def run(robot_count: int = 5, seconds: int = 60) -> None:
    init_db()
    db = SessionLocal()
    try:
        company = db.scalar(select(Company).limit(1))
        if company is None:
            raise SystemExit("Seed users first: python -m scripts.seed_users")
        admin = db.scalar(select(User).where(User.company_id == company.id))
        robots = []
        for index in range(robot_count):
            robot = Robot(
                company_id=company.id,
                name=f"Load test {index + 1}",
                serial_number=f"LOAD-{secrets.token_hex(4)}",
                api_key_hash=hash_robot_key(secrets.token_urlsafe(16)),
                api_key_prefix="loadtest",
            )
            db.add(robot)
            robots.append(robot)
        db.commit()
        robot_ids = [robot.id for robot in robots]
    finally:
        db.close()

    latencies: list[float] = []
    errors: list[str] = []
    lock = threading.Lock()

    def worker(robot_id: int) -> None:
        session = SessionLocal()
        try:
            for _ in range(seconds):
                started = time.perf_counter()
                try:
                    insert_telemetry(
                        session,
                        robot_id=robot_id,
                        ts=datetime.now(timezone.utc),
                        lat=35.8256,
                        lng=10.6369,
                        battery_pct=88.0,
                        status="active",
                    )
                    with lock:
                        latencies.append((time.perf_counter() - started) * 1000)
                except Exception as exc:  # pragma: no cover - operational script
                    with lock:
                        errors.append(str(exc))
                time.sleep(max(0.0, 1.0 - (time.perf_counter() - started)))
        finally:
            session.close()

    threads = [threading.Thread(target=worker, args=(robot_id,)) for robot_id in robot_ids]
    started = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed = time.perf_counter() - started

    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies or [0])
    print(f"Inserted {len(latencies)} rows in {elapsed:.1f}s ({robot_count} robots at 1 Hz).")
    print(f"p95 insert time: {p95:.1f} ms")
    if errors:
        print(f"Errors: {len(errors)} (first: {errors[0]})")

    cleanup = SessionLocal()
    try:
        cleanup.execute(delete(Telemetry).where(Telemetry.robot_id.in_(robot_ids)))
        cleanup.execute(delete(Robot).where(Robot.id.in_(robot_ids)))
        cleanup.commit()
        print("Temporary robots and their telemetry removed.")
    finally:
        cleanup.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robots", type=int, default=5)
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()
    run(robot_count=args.robots, seconds=args.seconds)


if __name__ == "__main__":
    main()
