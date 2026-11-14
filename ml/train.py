"""Train the incident prediction model.

    python train.py [--data ml/data/hourly_dataset.csv]

Chronological 80/20 split, two baselines, logistic regression and a random
forest. The decision threshold is chosen on a validation slice taken from the
end of the training set, never on the test set. The best model by PR-AUC is
saved to ``ml/models/incident_model.joblib`` with ``metrics.json`` beside it.
"""

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    roc_auc_score,
)

ML_ROOT = Path(__file__).resolve().parent
DATA_FILE = ML_ROOT / "data" / "hourly_dataset.csv"
MODEL_DIR = ML_ROOT / "models"
DOCS_DIR = ML_ROOT.parent / "docs"
FEATURES = ["hour_sin", "hour_cos", "dow", "is_weekend", "is_night"]


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add the calendar features in the exact order the API builds them."""
    data = frame.copy()
    hour = data["hour"].astype(int)
    data["hour_sin"] = np.sin(2 * math.pi * hour / 24)
    data["hour_cos"] = np.cos(2 * math.pi * hour / 24)
    data["dow"] = data["dow"].astype(int)
    data["is_weekend"] = data["is_weekend"].astype(int)
    data["is_night"] = data["is_night"].astype(int)
    return data


def load_dataset(path: Path = DATA_FILE) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["ts_hour"] = pd.to_datetime(frame["ts_hour"], utc=True, errors="raise")
    frame = frame.sort_values("ts_hour").reset_index(drop=True)
    return add_features(frame)


def chronological_split(frame: pd.DataFrame, fraction: float = 0.8):
    """Split by time order; never shuffle, or the future leaks into training."""
    split = max(1, int(len(frame) * fraction))
    return frame.iloc[:split].copy(), frame.iloc[split:].copy()


def _metrics(name: str, y_true, probabilities, threshold: float) -> dict:
    predictions = (np.asarray(probabilities) >= threshold).astype(int)
    both_classes = len(set(y_true)) > 1
    return {
        "model": name,
        "threshold": round(float(threshold), 3),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4) if both_classes else None,
        "pr_auc": round(float(average_precision_score(y_true, probabilities)), 4),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
        "brier": round(float(brier_score_loss(y_true, probabilities)), 4),
    }


def _best_threshold(y_true, probabilities) -> float:
    best, best_f1 = 0.5, -1.0
    for candidate in np.linspace(0.02, 0.98, 97):
        score = f1_score(y_true, (np.asarray(probabilities) >= candidate).astype(int), zero_division=0)
        if score > best_f1:
            best, best_f1 = float(candidate), score
    return best


def _baseline_rate(train: pd.DataFrame) -> np.ndarray:
    rate = float(train["incident"].mean())
    return np.full(len(train), rate)


def train_pipeline(
    frame: pd.DataFrame,
    trees: int = 200,
    model_dir: Path = MODEL_DIR,
    docs_dir: Path = DOCS_DIR,
    write: bool = True,
) -> dict:
    """Fit baselines and models, save the best one, and return the metrics dict."""
    train, test = chronological_split(frame)
    if train.empty or test.empty:
        raise SystemExit("Not enough hourly rows to train. Generate at least a few days.")

    x_train, y_train = train[FEATURES], train["incident"].astype(int)
    x_test, y_test = test[FEATURES], test["incident"].astype(int)

    # Validation slice for the threshold: the last 20% of the training window.
    core_end = max(1, int(len(train) * 0.8))
    core, validation = train.iloc[:core_end], train.iloc[core_end:]
    if validation.empty:
        validation = core.tail(max(1, len(core) // 5))

    rows: list[dict] = []

    # Baseline A: always predict the training incident rate.
    rate = float(y_train.mean())
    rows.append(_metrics("baseline_rate", y_test, np.full(len(test), rate), 0.5))

    # Baseline B: historical rate for each (day-of-week, hour) pair.
    pair_rate = train.groupby(["dow", "hour"])["incident"].mean()
    fallback = rate
    baseline_b = [
        float(pair_rate.get((int(dow), int(hour)), fallback))
        for dow, hour in zip(test["dow"], test["hour"])
    ]
    rows.append(_metrics("baseline_dow_hour", y_test, baseline_b, 0.5))

    candidates = {
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=trees,
            class_weight="balanced",
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
    }

    fitted: dict[str, object] = {}
    thresholds: dict[str, float] = {}

    for name, model in candidates.items():
        # Threshold search happens on the validation slice only.
        probe = model.__class__(**model.get_params())
        probe.fit(core[FEATURES], core["incident"].astype(int))
        if validation.empty:
            thresholds[name] = 0.5
        else:
            validated = probe.predict_proba(validation[FEATURES])[:, 1]
            thresholds[name] = _best_threshold(validation["incident"].astype(int), validated)

        model.fit(x_train, y_train)
        fitted[name] = model
        rows.append(_metrics(name, y_test, model.predict_proba(x_test)[:, 1], thresholds[name]))

    model_rows = [row for row in rows if row["model"] in candidates]
    best_row = max(model_rows, key=lambda row: row["pr_auc"])
    best_name = best_row["model"]
    best_model = fitted[best_name]

    importance = _importance(best_model, best_name)
    if write:
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(best_model, model_dir / "incident_model.joblib")

    payload = {
        "best_model": best_name,
        "threshold": thresholds[best_name],
        "features": FEATURES,
        "metrics": rows,
        "train_range": [
            train["ts_hour"].iloc[0].isoformat(),
            train["ts_hour"].iloc[-1].isoformat(),
        ],
        "test_range": [
            test["ts_hour"].iloc[0].isoformat(),
            test["ts_hour"].iloc[-1].isoformat(),
        ],
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "incident_rate": round(float(y_train.mean()), 4),
        "feature_importance": importance,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "note": (
            "Trained on real alerts plus synthetic incidents. Synthetic history "
            "is fabricated, so these scores show the method, not real-world skill."
        ),
    }

    if write:
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _plot_importance(importance, docs_dir)

    return payload


def _importance(model, name: str) -> dict[str, float]:
    if name == "random_forest" and hasattr(model, "feature_importances_"):
        values = model.feature_importances_
    elif hasattr(model, "coef_"):
        values = np.abs(model.coef_[0])
    else:
        values = np.ones(len(FEATURES))
    total = float(np.sum(values)) or 1.0
    return {feature: round(float(value / total), 4) for feature, value in zip(FEATURES, values)}


def _plot_importance(importance: dict[str, float], docs_dir: Path) -> None:
    try:
        docs_dir.mkdir(parents=True, exist_ok=True)
        ordered = dict(sorted(importance.items(), key=lambda item: item[1]))
        figure, axis = plt.subplots(figsize=(7, 3.6))
        axis.barh(list(ordered.keys()), list(ordered.values()), color="#5B74E0")
        axis.set_xlabel("Relative importance")
        axis.set_title("Incident model · feature importance", loc="left", fontsize=12)
        axis.spines[["top", "right"]].set_visible(False)
        figure.tight_layout()
        figure.savefig(docs_dir / "feature_importance.png", dpi=150)
        plt.close(figure)
    except Exception as exc:  # noqa: BLE001 - a plot is documentation, not training
        print(f"Warning: could not write the importance plot ({exc}).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_FILE)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DOCS_DIR)
    parser.add_argument("--trees", type=int, default=200)
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"{args.data} is missing. Run build_dataset.py first.")

    frame = load_dataset(args.data)
    payload = train_pipeline(frame, trees=args.trees, model_dir=args.model_dir, docs_dir=args.docs_dir)

    print(f"Rows: {payload['train_rows']} train / {payload['test_rows']} test")
    print(f"Train window: {payload['train_range'][0]} -> {payload['train_range'][1]}")
    print(f"Test window:  {payload['test_range'][0]} -> {payload['test_range'][1]}")
    print()
    print(f"{'model':<22}{'accuracy':>10}{'roc_auc':>10}{'pr_auc':>10}{'f1':>8}{'brier':>8}")
    for row in payload["metrics"]:
        roc = f"{row['roc_auc']:.4f}" if row["roc_auc"] is not None else "n/a"
        print(
            f"{row['model']:<22}{row['accuracy']:>10.4f}{roc:>10}"
            f"{row['pr_auc']:>10.4f}{row['f1']:>8.4f}{row['brier']:>8.4f}"
        )
    print()
    print(f"Best model: {payload['best_model']} at threshold {payload['threshold']:.3f}")
    print(f"Saved to {args.model_dir / 'incident_model.joblib'}")


if __name__ == "__main__":
    main()
