"""Tests for the incident dataset and model pipeline."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_dataset  # noqa: E402
import clean  # noqa: E402
import train  # noqa: E402


def _incidents(rows: list[tuple[datetime, str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "robot_id": 1,
                "type": incident_type,
                "ts": ts,
                "lat": lat,
                "lng": lng,
                "source": "synthetic",
            }
            for ts, incident_type, lat, lng in rows
        ]
    )


def test_hourly_grid_has_no_gaps():
    start = datetime(2026, 1, 1, 3, tzinfo=timezone.utc)
    frame = _incidents(
        [
            (start + timedelta(minutes=10), "obstacle", 35.8, 10.6),
            (start + timedelta(hours=5), "intrusion", 35.8, 10.6),
        ]
    )

    grid = build_dataset.build_hourly(frame)

    stamps = pd.to_datetime(grid["ts_hour"])
    gaps = stamps.diff().dropna()
    assert len(grid) == 6
    assert (gaps == pd.Timedelta(hours=1)).all()


def test_cleaning_removes_duplicates_and_bad_rows():
    start = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    frame = _incidents(
        [
            (start, "obstacle", 35.8, 10.6),
            (start + timedelta(seconds=1), "obstacle", 35.8, 10.6),
            (start + timedelta(seconds=30), "obstacle", 35.8, 10.6),
            (start + timedelta(minutes=5), "rain", 35.8, 10.6),
            (start + timedelta(minutes=9), "intrusion", 120.0, 10.6),
        ]
    )
    frame.loc[len(frame)] = {
        "robot_id": 1,
        "type": "intrusion",
        "ts": None,
        "lat": 35.8,
        "lng": 10.6,
        "source": "real",
    }

    cleaned = clean.clean_incidents(frame)

    assert len(cleaned) == 2
    assert set(cleaned["type"]) == {"obstacle"}
    assert cleaned["ts"].is_monotonic_increasing


def test_incident_flag_matches_count():
    start = datetime(2026, 2, 1, tzinfo=timezone.utc)
    frame = _incidents(
        [
            (start + timedelta(minutes=5), "obstacle", 35.8, 10.6),
            (start + timedelta(minutes=15), "intrusion", 35.8, 10.6),
            (start + timedelta(hours=2), "obstacle", 35.8, 10.6),
        ]
    )

    grid = build_dataset.build_hourly(frame)

    assert list(grid["incident"]) == [1, 0, 1]
    assert list(grid["incident_count"]) == [2, 0, 1]
    assert (grid["incident"] == (grid["incident_count"] > 0).astype(int)).all()


def _training_frame(hours: int = 900) -> pd.DataFrame:
    start = datetime(2025, 6, 1, tzinfo=timezone.utc)
    stamps = [start + timedelta(hours=offset) for offset in range(hours)]
    frame = pd.DataFrame(
        {
            "ts_hour": stamps,
            "hour": [stamp.hour for stamp in stamps],
            "dow": [stamp.weekday() for stamp in stamps],
        }
    )
    frame["is_weekend"] = (frame["dow"] >= 5).astype(int)
    frame["is_night"] = ((frame["hour"] >= 22) | (frame["hour"] < 6)).astype(int)
    frame["incident_count"] = frame["is_night"] * 2
    frame["incident"] = (frame["incident_count"] > 0).astype(int)
    return train.add_features(frame)


def test_split_is_chronological():
    frame = _training_frame(100)
    train_part, test_part = train.chronological_split(frame)

    assert len(train_part) == 80
    assert len(test_part) == 20
    assert train_part["ts_hour"].max() < test_part["ts_hour"].min()


def test_saved_model_loads_and_predicts_24_hours(tmp_path):
    frame = _training_frame()
    payload = train.train_pipeline(frame, trees=8, model_dir=tmp_path, docs_dir=tmp_path, write=True)

    path = tmp_path / "incident_model.joblib"
    assert path.exists()

    model = joblib.load(path)
    future = train.add_features(frame.head(0).copy())
    start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    rows = []
    for offset in range(24):
        moment = start + timedelta(hours=offset)
        rows.append(
            {
                "hour": moment.hour,
                "dow": moment.weekday(),
                "is_weekend": int(moment.weekday() >= 5),
                "is_night": int(moment.hour >= 22 or moment.hour < 6),
            }
        )
    future = train.add_features(pd.DataFrame(rows))

    probabilities = model.predict_proba(future[train.FEATURES])[:, 1]

    assert probabilities.shape == (24,)
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    assert 0 <= payload["threshold"] <= 1
    assert payload["best_model"] in {"logistic_regression", "random_forest"}
