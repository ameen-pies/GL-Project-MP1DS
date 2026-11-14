"""Export alerts from the operational database to ``ml/data/raw_incidents.csv``.

    python export_incidents.py [--company-id 1] [--database-url URL]

The database defaults to the backend's SQLite file, so the pipeline works from
a clean checkout. Nothing is invented here: ``source`` is always ``real``.
"""

import argparse
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

ML_ROOT = Path(__file__).resolve().parent
REPO_ROOT = ML_ROOT.parent
DATA_DIR = ML_ROOT / "data"
OUT_FILE = DATA_DIR / "raw_incidents.csv"
COLUMNS = ["robot_id", "type", "ts", "lat", "lng", "source"]
DEFAULT_DATABASE = f"sqlite:///{(REPO_ROOT / 'backend' / 'fleet.db').as_posix()}"


def _iso(value) -> str:
    """Normalise a stored timestamp to UTC ISO-8601 with a Z suffix."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def export_incidents(
    database_url: str | None = None,
    company_id: int | None = None,
    out_file: Path = OUT_FILE,
) -> int:
    """Write every alert as a CSV row and return the number exported."""
    url = database_url or os.environ.get("DATABASE_URL") or DEFAULT_DATABASE
    out_file.parent.mkdir(parents=True, exist_ok=True)

    sql = "SELECT robot_id, type, ts, lat, lng FROM alerts"
    params: dict = {}
    if company_id is not None:
        sql += " WHERE company_id = :company_id"
        params["company_id"] = company_id
    sql += " ORDER BY ts"

    rows: list[dict] = []
    try:
        engine = create_engine(url)
        with engine.connect() as connection:
            for record in connection.execute(text(sql), params):
                rows.append(
                    {
                        "robot_id": record.robot_id,
                        "type": record.type,
                        "ts": _iso(record.ts),
                        "lat": record.lat,
                        "lng": record.lng,
                        "source": "real",
                    }
                )
        engine.dispose()
    except Exception as exc:  # noqa: BLE001 - exporting must not crash the pipeline
        print(f"Warning: could not read alerts ({exc}). Writing an empty real set.")

    with out_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} real incidents to {out_file}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=None, help="SQLAlchemy database URL")
    parser.add_argument("--company-id", type=int, default=None, help="export one company only")
    parser.add_argument("--out", type=Path, default=OUT_FILE)
    args = parser.parse_args()
    export_incidents(args.database_url, args.company_id, args.out)


if __name__ == "__main__":
    main()
