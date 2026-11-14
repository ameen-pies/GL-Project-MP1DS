# Incident dataset and model

This folder builds the hourly incident dataset and trains the model behind the
**Risk forecast** page.

> The synthetic incidents are made up. The model results therefore demonstrate
> the method and the pipeline, not real-world performance. Say the same thing in
> any report or demo that quotes these numbers.

## Run the pipeline in order

```bash
cd ml
python export_incidents.py
python generate_fake_incidents.py --days 180 --seed 42
python clean.py
python build_dataset.py
python train.py
```

| Script | What it does | Output |
|---|---|---|
| `export_incidents.py` | reads the `alerts` table (all companies, or `--company-id`) | `data/raw_incidents.csv` |
| `generate_fake_incidents.py` | seeded Poisson incidents, higher 22:00–05:59 and on weekends | `data/fake_incidents.csv` |
| `clean.py` | parses UTC timestamps; drops missing/invalid rows, bad types, out-of-range coordinates, and same-robot/type duplicates within 1 s | `data/cleaned_incidents.csv` |
| `build_dataset.py` | floors to the hour and builds a **complete** hourly grid, zero-filled | `data/hourly_dataset.csv` |
| `train.py` | chronological 80/20 split, two baselines, logistic regression, random forest, metrics, saved model | `models/incident_model.joblib`, `models/metrics.json`, `docs/feature_importance.png` |

`data/` and `models/` are git-ignored; regenerate them on a new machine.

## Dataset columns

| Column | Meaning |
|---|---|
| `ts_hour` | UTC hour, ISO-8601 with `Z` |
| `hour` | 0–23 |
| `dow` | day of week, 0 = Monday |
| `is_weekend` | 1 when `dow >= 5` |
| `is_night` | 1 when the hour is 22:00–05:59 |
| `incident_count` | incidents in that hour |
| `incident` | 1 when `incident_count > 0`, otherwise 0 |

## Model and metrics

`train.py` writes `models/metrics.json` with `best_model`, the decision
`threshold`, the ordered `features`, the full metrics table, and the train/test
ranges. The backend loads both files at request time (cached for 60 minutes) and
uses the same five features:

```
hour_sin, hour_cos, dow, is_weekend, is_night
```

See [`../docs/ml-report.md`](../docs/ml-report.md) for the results table,
feature importance, and limitations.

## Tests

```bash
cd ml
python -m pytest tests -q
```

The tests cover the gap-free hourly grid, the cleaning rules, the incident flag,
the chronological split, and a saved model that loads and returns 24 valid
probabilities.
