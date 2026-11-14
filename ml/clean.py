"""Merge, validate, and de-duplicate real and synthetic incidents.

    python clean.py

Reads ``ml/data/raw_incidents.csv`` and ``ml/data/fake_incidents.csv`` (either
may be missing) and writes ``ml/data/cleaned_incidents.csv``.
"""

from pathlib import Path

import pandas as pd

ML_ROOT = Path(__file__).resolve().parent
DATA_DIR = ML_ROOT / "data"
CLEAN_FILE = DATA_DIR / "cleaned_incidents.csv"
COLUMNS = ["robot_id", "type", "ts", "lat", "lng", "source"]
VALID_TYPES = {"intrusion", "obstacle"}


def clean_incidents(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop unusable rows and near-duplicate reports, printing each rule's count."""
    data = frame.copy()
    if data.empty:
        print("No incident rows to clean.")
        return pd.DataFrame(columns=COLUMNS)

    for column in COLUMNS:
        if column not in data.columns:
            data[column] = pd.NA

    total = len(data)

    data["ts"] = pd.to_datetime(data["ts"], utc=True, errors="coerce")
    missing_ts = int(data["ts"].isna().sum())
    data = data.dropna(subset=["ts"])
    print(f"Removed {missing_ts} rows with a missing or invalid timestamp")

    valid_type = data["type"].isin(VALID_TYPES)
    invalid_types = int((~valid_type).sum())
    data = data[valid_type]
    print(f"Removed {invalid_types} rows with an unknown incident type")

    coordinates = (
        pd.to_numeric(data["lat"], errors="coerce").between(-90, 90)
        & pd.to_numeric(data["lng"], errors="coerce").between(-180, 180)
    )
    invalid_coordinates = int((~coordinates).sum())
    data = data[coordinates]
    print(f"Removed {invalid_coordinates} rows with coordinates out of range")

    data = data.sort_values(["robot_id", "type", "ts"]).reset_index(drop=True)
    gap = data.groupby(["robot_id", "type"])["ts"].diff()
    duplicate = gap.notna() & (gap <= pd.Timedelta(seconds=1))
    duplicates = int(duplicate.sum())
    data = data[~duplicate]
    print(f"Removed {duplicates} duplicate reports (same robot, type, within 1 s)")

    data = data[COLUMNS].reset_index(drop=True)
    print(f"Kept {len(data)} of {total} rows")
    return data


def main() -> None:
    sources = []
    for name in ("raw_incidents.csv", "fake_incidents.csv"):
        path = DATA_DIR / name
        if path.exists():
            sources.append(pd.read_csv(path))
            print(f"Loaded {path}")
        else:
            print(f"Skipped {path} (missing)")

    frame = pd.concat(sources, ignore_index=True) if sources else pd.DataFrame(columns=COLUMNS)
    cleaned = clean_incidents(frame)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(CLEAN_FILE, index=False)
    print(f"Wrote {len(cleaned)} rows to {CLEAN_FILE}")


if __name__ == "__main__":
    main()
