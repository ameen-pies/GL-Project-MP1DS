"""Build a complete hourly incident dataset with no missing hours.

    python build_dataset.py

Reads ``ml/data/cleaned_incidents.csv`` and writes
``ml/data/hourly_dataset.csv`` with one row per hour in the covered range.
"""

from pathlib import Path

import pandas as pd

ML_ROOT = Path(__file__).resolve().parent
DATA_DIR = ML_ROOT / "data"
CLEAN_FILE = DATA_DIR / "cleaned_incidents.csv"
DATASET_FILE = DATA_DIR / "hourly_dataset.csv"
COLUMNS = [
    "ts_hour",
    "hour",
    "dow",
    "is_weekend",
    "is_night",
    "incident_count",
    "incident",
]


def build_hourly(frame: pd.DataFrame) -> pd.DataFrame:
    """Return every hour between the first and last incident, zero-filled."""
    if frame.empty:
        return pd.DataFrame(columns=COLUMNS)

    data = frame.copy()
    data["ts"] = pd.to_datetime(data["ts"], utc=True, errors="coerce")
    data = data.dropna(subset=["ts"])
    if data.empty:
        return pd.DataFrame(columns=COLUMNS)

    hours = data["ts"].dt.floor("h")
    complete = pd.date_range(hours.min(), hours.max(), freq="h", tz="UTC")
    counts = hours.value_counts()

    grid = pd.DataFrame({"ts_hour": complete})
    grid["incident_count"] = (
        grid["ts_hour"].map(counts).fillna(0).astype(int)
    )
    grid["hour"] = grid["ts_hour"].dt.hour
    grid["dow"] = grid["ts_hour"].dt.weekday
    grid["is_weekend"] = (grid["dow"] >= 5).astype(int)
    grid["is_night"] = ((grid["hour"] >= 22) | (grid["hour"] < 6)).astype(int)
    grid["incident"] = (grid["incident_count"] > 0).astype(int)
    grid["ts_hour"] = grid["ts_hour"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return grid[COLUMNS]


def main() -> None:
    if not CLEAN_FILE.exists():
        raise SystemExit("Run clean.py first: ml/data/cleaned_incidents.csv is missing.")

    cleaned = pd.read_csv(CLEAN_FILE)
    dataset = build_hourly(cleaned)
    if dataset.empty:
        raise SystemExit("No usable incidents after cleaning; cannot build a dataset.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(DATASET_FILE, index=False)
    print(f"Wrote {len(dataset)} hourly rows to {DATASET_FILE}")
    print(f"Range: {dataset['ts_hour'].iloc[0]} to {dataset['ts_hour'].iloc[-1]}")
    print(f"Hours with at least one incident: {int(dataset['incident'].sum())}")


if __name__ == "__main__":
    main()
