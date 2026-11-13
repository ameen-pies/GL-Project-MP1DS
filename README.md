# Fleet Control

Patrol operations console for security robots. Built sprint by sprint from
[`fleet-control-spec-book.md`](fleet-control-spec-book.md).

## Stack (adapted)

| Layer | In the book | In this build |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind | Plain HTML, CSS, and JavaScript |
| Backend | FastAPI | FastAPI |
| Database | PostgreSQL 16 | SQLite |
| Tests | pytest | pytest (added in SCRUM-21) |

No build step, no npm, no Docker. FastAPI serves the static frontend and the API from one process.

## Run it

From the repo root:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://localhost:8000>.

Notes:

- The first run does not need a database. SQLite is wired in SCRUM-21.
- The frontend lives in `frontend/` and is mounted at `/`. API routes will live under `/api/v1`.
- Copy `.env.example` to `.env` when the backend starts reading configuration (SCRUM-21).

## Layout

```
backend/
  app/main.py            FastAPI app, static mount
  requirements.txt
frontend/
  index.html             Shell overview
  robots.html            Fleet registry (placeholder)
  map.html               Live map (placeholder)
  missions.html          Patrol missions (placeholder)
  alerts.html            Alerts (placeholder)
  analytics.html         Analytics (placeholder)
  predictions.html       Risk forecast (placeholder)
  css/tokens.css         OKLCH color, type, spacing, motion tokens
  css/base.css           Reset, buttons, chips, tables, forms
  css/layout.css         App frame, navigation, page layout
  js/layout.js           Shared header, navigation, UTC clock, footer
  js/pages.js            Placeholder content per module
PRODUCT.md               Users, purpose, anti-references, principles
DESIGN.md                Visual system and component rules
```

## Progress

- [x] Project shell: design tokens, responsive navigation, overview, placeholder pages
- [ ] SCRUM-21 Set up repo, CI, and database
- [ ] SCRUM-20 Log in with roles
- [ ] SCRUM-22 Register a robot to the fleet
- [ ] SCRUM-23 Robot list page
- [ ] SCRUM-24 Set up telemetry storage
- [ ] SCRUM-25 Receive robot telemetry through an API
- [ ] SCRUM-26 Show robot position on a live map
- [ ] SCRUM-27 Battery and status panel
- [ ] SCRUM-28 Define the mission data model
- [ ] SCRUM-29 Start and stop a mission remotely
- [ ] SCRUM-30 Set up the email sending service
- [ ] SCRUM-31 Trigger an alert on intrusion or obstacle
- [ ] SCRUM-32 Write the statistics queries
- [ ] SCRUM-33 Weekly patrol summary chart
- [ ] SCRUM-35 Prepare the incident dataset
- [ ] SCRUM-36 Train the incident prediction model
- [ ] SCRUM-37 See predicted high-risk time slots

## Workflow

Each issue gets a branch such as `feature/SCRUM-21-setup-repo-ci`, commits that start with the
Jira key, and a pull request titled with the same key. The shell commit is the base that
SCRUM-21 builds on.
