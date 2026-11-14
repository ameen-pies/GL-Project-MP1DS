"""Generate reproducible synthetic incidents for training.

    python generate_fake_incidents.py --days 180 --seed 42

The synthetic data is made up. It exists so the pipeline can be exercised when
real alert history is too small; results demonstrate the method, not reality.
"""

import argparse
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ML_ROOT = Path(__file__).resolve().parent
OUT_FILE = ML_ROOT / "data" / "fake_incidents.csv"
COLUMNS = ["robot_id", "type", "ts", "lat", "lng", "source"]
SOUSSE = (35.8256, 10.6369)


def hourly_rate(hour: int, weekday: int) -> float:
    """Poisson rate per hour: quiet by day, busy at night, a lift on weekends."""
    rate = 0.4 if hour >= 22 or hour < 6 else 0.05
    if weekday >= 5:
        rate *= 1.35
    return rate


def generate(days: int = 180, seed: int = 42, out_file: Path = OUT_FILE) -> int:
    rng = np.random.default_rng(seed)
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)

    rows: list[dict] = []
    moment = start
    while moment < end:
        count = int(rng.poisson(hourly_rate(moment.hour, moment.weekday())))
        for _ in range(count):
            ts = moment + timedelta(
                seconds=int(rng.integers(0, 3600)),
                microseconds=int(rng.integers(0, 1_000_000)),
            )
            # 70% obstacles, 30% intrusions.
            incident_type = "obstacle" if rng.random() < 0.7 else "intrusion"
            rows.append(
                {
                    "robot_id": int(rng.integers(1, 6)),
                    "type": incident_type,
                    "ts": ts.isoformat().replace("+00:00", "Z"),
                    "lat": round(float(SOUSSE[0] + rng.uniform(-0.004, 0.004)), 6),
                    "lng": round(float(SOUSSE[1] + rng.uniform(-0.004, 0.004)), 6),
                    "source": "synthetic",
                }
            )
        moment += timedelta(hours=1)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} synthetic incidents over {days} days to {out_file}")
    print("Reminder: synthetic rows are fabricated; model results are methodological only.")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=OUT_FILE)
    args = parser.parse_args()
    generate(args.days, args.seed, args.out)


if __name__ == "__main__":
    main()
