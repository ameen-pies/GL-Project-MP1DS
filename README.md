# Fleet Control

Patrol operations console for security robots. Built sprint by sprint from
[`fleet-control-spec-book.md`](fleet-control-spec-book.md), with the visual
system in [`DESIGN.md`](DESIGN.md) and [`PRODUCT.md`](PRODUCT.md).

## Stack (adapted)

| Layer | In the book | In this build |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind | Plain HTML, CSS, and JavaScript |
| Maps / charts | react-leaflet / Recharts | Leaflet (CDN) / hand-built SVG |
| Backend | FastAPI | FastAPI |
| Database | PostgreSQL 16 + Alembic | SQLite, schema from the SQLAlchemy models |
| Mail | Mailpit / SMTP | `smtplib`, Mailpit-compatible settings |
| ML | scikit-learn | scikit-learn (same) |

No build step, no npm, no Docker. FastAPI serves the static frontend and the API
from one process. Every sprints' behaviour is implemented; only the delivery
tooling differs from the book (no Vite, no Postgres, no Alembic).

## Run it

From the repo root:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env
python -m scripts.seed_users
python -m scripts.seed_routes
uvicorn app.main:app --reload
```

Open <http://localhost:8000>.

### Demo accounts

| Email | Role | Password |
|---|---|---|
| `admin@demo.tn` | admin | `Admin123!` (`SEED_ADMIN_PASSWORD`) |
| `operator@demo.tn` | operator | `Operator123!` (`SEED_OPERATOR_PASSWORD`) |
| `admin@other.tn` | admin, second company | `Admin123!` |

`admin@other.tn` exists to prove company isolation: it sees none of the demo
company's robots, missions, or alerts.

### Pages

| Route | What it does |
|---|---|
| `/login.html` | JWT login; redirects back to the requested page |
| `/robots.html` | company fleet, debounced name search, status and battery |
| `/robot-new.html` | admin-only registration; API key shown once |
| `/map.html` | Leaflet map, 5-second polling, status/battery panel |
| `/missions.html` | create from a seeded route, start/stop, event log |
| `/alerts.html` | open/all queue, acknowledge, 10-second polling |
| `/analytics.html` | weekly stacked bars, previous/next week |
| `/predictions.html` | next 24 hours of incident risk |

The overview at `/` is public. Every other page requires a login and polls only
the signed-in user's company.

### Simulator

Register a robot in the UI, copy its key, then from `backend/`:

```bash
python -m scripts.simulator --api-url http://localhost:8000 --key <KEY> --interval 2 --events
```

Pass `--key` several times to simulate a fleet. The simulator random-walks,
follows a running mission's route, drains battery, and (with `--events`) raises
occasional obstacle/intrusion alerts. A robot turns **offline** after 60 seconds
without a sample, so stop the simulator and watch the status change.

### Demo data

```bash
cd backend
python -m scripts.seed_demo_data --reset
```

Five robots, ~300k telemetry rows over seven days, ~40 finished missions, and 18
alerts. Useful for the analytics chart and the alert queue.

### Email

`services/email.py` uses `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`,
and `EMAIL_FROM`. Mailpit (SMTP `:1025`, UI `:8025`) works by pointing the env
vars at it; a real provider needs only those env vars and `SMTP_USER` set (which
enables TLS login). Sending never raises: failures are logged and the alert is
still stored. To check the transport without a robot:

```bash
cd backend
python -m scripts.send_test_email you@example.com
```

### Risk forecast

The page needs a trained model:

```bash
cd ml
python export_incidents.py
python generate_fake_incidents.py --days 180 --seed 42
python clean.py
python build_dataset.py
python train.py
```

Then reload `/predictions.html`. Missing model → `503` with the training
command. See [`docs/ml-report.md`](docs/ml-report.md) for results and the
synthetic-data caveat.

## Tests

```bash
cd backend && python -m pytest -q
cd ml && python -m pytest tests -q
```

42 backend tests cover auth and roles, company isolation, robot registration,
telemetry ingestion, the status rule, missions, alerts, analytics, and
predictions. 5 ML tests cover the hourly grid, cleaning, split order, and model
round-trip.

## Layout

```
backend/
  app/main.py            FastAPI app, static mount
  app/api/               health, auth, robots, robot_api, missions, alerts,
                         analytics, predictions
  app/core/              config, security, dependencies
  app/db/                engine, session, schema creation
  app/models/            SQLAlchemy models
  app/schemas/           Pydantic payloads
  app/services/          status rule, telemetry repo, missions, alerts, email,
                         prediction
  app/analytics/         statistics queries
  scripts/               seed_users, seed_routes, seed_demo_data, simulator,
                         telemetry_load_test, send_test_email
  tests/                 pytest suite
frontend/
  index.html             public overview
  login.html             login
  robots.html            fleet registry
  robot-new.html         register a robot
  map.html               live map
  missions.html          patrol missions
  alerts.html            alert queue
  analytics.html         weekly chart
  predictions.html       risk forecast
  css/tokens.css         color, type, spacing, shape, motion tokens
  css/base.css           reset, buttons, chips, tables, forms
  css/layout.css         editorial shell, hero, sections, footer
  css/app.css            operational pages (tables, map, chart, risk)
  js/api.js              session, API wrapper, shared render helpers
  js/layout.js           header, nav, alert badge, clock, health, footer
  js/pages.js            overview module fan
  js/<page>.js           one script per page
ml/                      export, synthetic data, clean, dataset, train, tests
docs/                    data-model.md, ml-report.md, feature_importance.png
.github/workflows/ci.yml backend tests on every PR
PRODUCT.md               users, purpose, anti-references, principles
DESIGN.md                visual system and component rules
```

## Progress

- [x] SCRUM-21 Set up repo, CI, and database (adapted: SQLite, static frontend)
- [x] SCRUM-20 Log in with roles
- [x] SCRUM-22 Register a robot to the fleet
- [x] SCRUM-23 Robot list page
- [x] SCRUM-24 Set up telemetry storage
- [x] SCRUM-25 Receive robot telemetry through an API
- [x] SCRUM-26 Show robot position on a live map
- [x] SCRUM-27 Battery and status panel
- [x] SCRUM-28 Define the mission data model
- [x] SCRUM-29 Start and stop a mission remotely
- [x] SCRUM-30 Set up the email sending service
- [x] SCRUM-31 Trigger an alert on intrusion or obstacle
- [x] SCRUM-32 Write the statistics queries
- [x] SCRUM-33 Weekly patrol summary chart
- [x] SCRUM-35 Prepare the incident dataset
- [x] SCRUM-36 Train the incident prediction model
- [x] SCRUM-37 See predicted high-risk time slots

## Workflow

Each issue gets a branch such as `feature/SCRUM-21-setup-repo-ci`, commits that
start with the Jira key, and a pull request titled with the same key.
