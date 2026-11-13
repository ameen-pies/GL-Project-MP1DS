# Fleet Control: Specification Book

**Jira space:** SCRUM (My Data Science Team) · **GitHub:** `github.com/ameen-pies/fleet-control` (to create) · **Sprints:** 4 × 2 weeks (Nov 11, 2026 to Jan 5, 2027)

Fleet Control is a web platform to supervise security patrol robots: live map, patrol missions, alerts, analytics, and an incident prediction model. The case is inspired by Enova Robotics (Tunisian robotics startup). **It is an invented practice project, not Enova's real roadmap.**

> Assumed stack (change it before starting if you prefer another): **FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL 16** (backend), **React 18 + TypeScript + Vite + Tailwind** (frontend), **scikit-learn** (prediction), **GitHub Actions** (CI), **Docker Compose** for Postgres and a dev mail server.

---

## 0. How to use this book

1. Read sections 1 to 8 once. They are the rules every issue follows.
2. Work through the issues **in the order listed** (Sprint 1 → 4). Each issue section contains: goal, dependencies, branch name, Jira steps, build steps, API contract, tests, acceptance checklist, PR title, and an AI prompt.
3. For every issue, do the **Jira/GitHub loop** from section 3. This is what keeps GitHub linked to Jira.
4. If you generate code with an AI assistant, give it **this whole file once**, then paste the issue's "AI prompt" block. Always ask it to follow sections 1 to 8.
5. Never start an issue before its dependencies are merged into `main`.

### Jira issue map

| Sprint | Key | Type | Pts | Title | Epic |
|---|---|---|---|---|---|
| 1 | SCRUM-21 | Task | 3 | Set up repo, CI, and database | SCRUM-5 Fleet & user access |
| 1 | SCRUM-20 | Story | 5 | Log in with roles | SCRUM-5 |
| 1 | SCRUM-22 | Story | 3 | Register a robot to the fleet | SCRUM-5 |
| 1 | SCRUM-23 | Story | 5 | Robot list page | SCRUM-5 |
| 2 | SCRUM-24 | Task | 3 | Set up telemetry storage | SCRUM-6 Live robot monitoring |
| 2 | SCRUM-25 | Story | 5 | Receive robot telemetry through an API | SCRUM-6 |
| 2 | SCRUM-26 | Story | 5 | Show robot position on a live map | SCRUM-6 |
| 2 | SCRUM-27 | Story | 3 | Battery and status panel | SCRUM-6 |
| 3 | SCRUM-28 | Task | 2 | Define the mission data model | SCRUM-7 Patrol missions |
| 3 | SCRUM-29 | Story | 3 | Start and stop a mission remotely | SCRUM-7 |
| 3 | SCRUM-30 | Task | 2 | Set up the email sending service | SCRUM-8 Alerts & incidents |
| 3 | SCRUM-31 | Story | 5 | Trigger an alert on intrusion or obstacle | SCRUM-8 |
| 3 | SCRUM-32 | Task | 3 | Write the statistics queries | SCRUM-9 Analytics & reporting |
| 4 | SCRUM-33 | Story | 3 | Weekly patrol summary chart | SCRUM-9 |
| 4 | SCRUM-35 | Task | 3 | Prepare the incident dataset | SCRUM-34 Incident prediction |
| 4 | SCRUM-36 | Task | 5 | Train the incident prediction model | SCRUM-34 |
| 4 | SCRUM-37 | Story | 5 | See predicted high-risk time slots | SCRUM-34 |

Sprint load: S1 = 16, S2 = 16, S3 = 15, S4 = 16 points.

**Two gaps in your Jira backlog that this book fills (so nothing is missing at build time):**
- There is no "simulator" item. Robots don't exist yet, so the **robot simulator is built inside SCRUM-25** and extended in SCRUM-29 and SCRUM-31. Add Jira *sub-tasks* if you want to track it separately.
- There is no "create a mission" item. **SCRUM-29 includes creating a mission from a predefined (seeded) route**, then starting and stopping it. Add a comment on SCRUM-29 saying so, and optionally edit its description.

---

## 1. Architecture

```
React app (Vite, :5173) ──/api proxy──> FastAPI (:8000) ──> PostgreSQL (:5432)
                                              ^
 Robot simulator (Python) ──X-Robot-Key──────┘        Mailpit (SMTP :1025, UI :8025)
 ML scripts (ml/) ── read alerts, train model ── joblib file ── loaded by FastAPI
```

- **Auth for humans:** JWT bearer token (HS256, 60 min). Roles: `admin`, `operator`.
- **Auth for robots:** per-robot API key sent in the `X-Robot-Key` header. Only a SHA-256 hash is stored.
- **Multi-tenancy:** every user, robot, route, mission, and alert belongs to a `company`. **Every query must filter by the current user's `company_id`.** A user must never see another company's data.
- **Live updates:** the frontend polls (map every 5 s, alerts every 10 s). No websockets.
- **Time:** store all timestamps in UTC (`timestamptz`). Display in the browser's local time.

## 2. Conventions

**Repository layout**
```
fleet-control/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/        # config.py, security.py, deps.py
│   │   ├── db/          # session.py, base.py
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic models
│   │   ├── api/v1/      # routers: health, auth, robots, robot_api, missions, alerts, analytics, predictions
│   │   ├── services/    # robot_status.py, email.py, missions.py, alerts.py, prediction.py
│   │   └── analytics/   # queries.py
│   ├── alembic/         # migrations
│   ├── scripts/         # seed_users.py, seed_routes.py, seed_demo_data.py, simulator.py, telemetry_load_test.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/client.ts
│       ├── auth/        # AuthContext.tsx, ProtectedRoute.tsx
│       ├── components/  # Layout, StatusBadge, BatteryBadge, StatusPanel
│       └── pages/       # LoginPage, RobotsPage, RobotNewPage, MapPage, MissionsPage, AlertsPage, AnalyticsPage, PredictionPage
├── ml/                  # data/, models/, export_incidents.py, generate_fake_incidents.py, clean.py, build_dataset.py, train.py, README.md
├── docs/                # data-model.md, ml-report.md
├── docker-compose.yml
├── .env.example
├── .github/workflows/ci.yml
└── README.md
```

**Backend rules**
- API prefix `/api/v1`. JSON only. Errors use FastAPI's default `{"detail": "message"}`.
- Status codes: `200/201` success, `401` not logged in, `403` wrong role, `404` not found (also for another company's object), `409` conflict, `422` validation.
- Use SQLAlchemy 2 style (`Mapped[...]`, `select()`), Pydantic v2 schemas, one router per resource.
- Every schema change goes through an **Alembic migration**. Never edit the database by hand.
- Passwords hashed with `bcrypt`. Never log secrets.
- Tests with `pytest` + `httpx`/`TestClient` against a real PostgreSQL test database.

**Frontend rules**
- TypeScript strict mode. One API client (`api/client.ts`) that adds the token and handles 401 by logging out.
- Server state with **TanStack Query**. Routing with **React Router**. Styling with **Tailwind**.
- Maps: **react-leaflet** with OpenStreetMap tiles. Charts: **Recharts**.
- Every page handles loading, empty, and error states.

**Naming**
- Python: `snake_case`. TypeScript: `camelCase` for variables, `PascalCase` for components. SQL tables: plural `snake_case`.
- Branches: `feature/SCRUM-<n>-<short-slug>` (always uppercase key).

## 3. Git and Jira workflow (do this for EVERY issue)

**Before the first issue:** in the Atlassian "GitHub for Jira" settings, edit the connected organization `ameen-pies` (pencil icon, "Only select repos connected") and **add the `fleet-control` repo**. Without this, Jira never sees your branches.

**Per-issue loop**

| Step | Where | Action |
|---|---|---|
| 1 | Jira | Open the issue. Move it from **To Do** to **In Progress**. |
| 2 | Git | `git checkout main && git pull` then `git checkout -b feature/SCRUM-21-setup-repo-ci` |
| 3 | Git | Commit often, **always starting with the key**: `SCRUM-21 add docker compose for postgres` |
| 4 | GitHub | Push and open a pull request titled `SCRUM-21 Set up repo, CI, and database`. Use the PR template below. |
| 5 | GitHub | Wait for CI to be green. Self-review the diff. Squash-merge into `main` (keep the key in the squash title). |
| 6 | Jira | Check the **Development** panel on the issue: it should show the branch, commits, and PR. Tick off the acceptance criteria and move the issue to **Done**. |

- **Create branch from Jira (optional):** on the issue, click **Create branch** in the Development panel. It makes a correctly named branch for you.
- **Smart commits (optional):** `SCRUM-21 #done` or `SCRUM-21 #comment tested locally` can update the issue from a commit message. Test it once on a throwaway commit; if it doesn't work in your space, move issues by hand.
- **Automation (optional):** Space settings → Automation, create rules such as "branch created → In Progress" and "pull request merged → Done".
- **If the Development panel stays empty:** key not uppercase, key missing from the branch/PR title, repo not connected (see above), or the sync needs a few minutes. Push a new commit to trigger it.

**Pull request template** (save as `.github/pull_request_template.md`)
```markdown
## Jira
[SCRUM-XX](https://projet-glfie.atlassian.net/browse/SCRUM-XX)

## What changed
-

## How to test
1.

## Checklist
- [ ] Acceptance criteria verified
- [ ] Tests added and passing
- [ ] CI is green
- [ ] Docs/README updated if needed
```

**Definition of done (applies to every issue)**
1. Every acceptance criterion is verified and ticked.
2. Tests added and passing locally and in CI.
3. Merged into `main` through a PR whose title starts with the Jira key.
4. Issue shows branch/commits/PR in its Development panel and is moved to **Done**.
5. README or docs updated if setup or behavior changed.

**Sprint ritual**
- *Start of sprint:* Backlog → **Start sprint** (close the empty "SCRUM Sprint 0" first, once). Confirm the sprint total matches section 0.
- *End of sprint:* check the board, **Complete sprint**, note the points actually finished, adjust the next sprint if needed, and write 3 bullets (went well, went badly, change next time).

## 4. Environment variables (`.env.example`)

```
DATABASE_URL=postgresql+psycopg://fleet:fleet@localhost:5432/fleet
TEST_DATABASE_URL=postgresql+psycopg://fleet:fleet@localhost:5432/fleet_test
SECRET_KEY=change-me-in-real-life
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=alerts@fleet-control.local
SEED_ADMIN_PASSWORD=Admin123!
SEED_OPERATOR_PASSWORD=Operator123!
```
Never commit `.env`. Commit only `.env.example`.

## 5. Data model

Created progressively: Sprint 1 (companies, users, robots), Sprint 2 (telemetry), Sprint 3 (routes, waypoints, missions, mission_events, alerts).

| Table | Columns |
|---|---|
| `companies` | `id` PK, `name`, `created_at` |
| `users` | `id` PK, `company_id` FK, `email` unique, `password_hash`, `full_name`, `role` (`admin`/`operator`), `email_notifications` bool default true, `created_at` |
| `robots` | `id` PK, `company_id` FK, `name`, `serial_number` unique, `api_key_hash`, `api_key_prefix`, `created_at` |
| `telemetry` | `id` bigserial PK, `robot_id` FK, `ts` timestamptz, `lat`, `lng`, `battery_pct` (0 to 100), `status` (`active`/`idle`), `received_at` · index `(robot_id, ts DESC)` |
| `routes` | `id` PK, `company_id` FK, `name`, `created_at` |
| `waypoints` | `id` PK, `route_id` FK, `seq` int, `lat`, `lng` · unique `(route_id, seq)` |
| `missions` | `id` PK, `company_id` FK, `robot_id` FK, `route_id` FK, `status` (`scheduled`/`running`/`completed`/`stopped`/`cancelled`), `scheduled_at`, `started_at`, `ended_at`, `created_by` FK users, `created_at` |
| `mission_events` | `id` PK, `mission_id` FK, `action` (`start`/`stop`), `user_id` FK, `ts` |
| `alerts` | `id` PK, `company_id` FK, `robot_id` FK, `type` (`intrusion`/`obstacle`), `lat`, `lng`, `ts`, `acknowledged` bool default false, `acknowledged_by` FK users null, `acknowledged_at` null · index `(company_id, acknowledged, ts DESC)` |

## 6. API surface (introduced by)

| Method and path | Auth | Introduced in |
|---|---|---|
| `GET /api/v1/health` | none | SCRUM-21 |
| `POST /api/v1/auth/login` · `GET /api/v1/auth/me` | none / user | SCRUM-20 |
| `GET /api/v1/admin/ping` | admin | SCRUM-20 |
| `POST /api/v1/robots` | admin | SCRUM-22 |
| `GET /api/v1/robots?search=` | user | SCRUM-23 |
| `POST /api/v1/robot/telemetry` | robot key | SCRUM-25 |
| `GET /api/v1/robots/latest` | user | SCRUM-26 |
| `GET /api/v1/routes` · `POST/GET /api/v1/missions` · `POST /api/v1/missions/{id}/start` · `POST /api/v1/missions/{id}/stop` | user | SCRUM-29 |
| `GET /api/v1/robot/mission` | robot key | SCRUM-29 |
| `POST /api/v1/robot/events` | robot key | SCRUM-31 |
| `GET /api/v1/alerts` · `GET /api/v1/alerts/open-count` · `POST /api/v1/alerts/{id}/acknowledge` | user | SCRUM-31 |
| `GET /api/v1/analytics/missions/weekly?week_offset=` | user | SCRUM-33 |
| `GET /api/v1/predictions/risk?hours=24` | user | SCRUM-37 |

## 7. Test accounts (created by `scripts/seed_users.py`)

| Email | Role | Password |
|---|---|---|
| `admin@demo.tn` | admin | value of `SEED_ADMIN_PASSWORD` |
| `operator@demo.tn` | operator | value of `SEED_OPERATOR_PASSWORD` |

Both belong to company "Demo Security SA". The seed script also creates a **second company** with its own admin (`admin@other.tn`) so you can test that data is isolated.

## 8. Standard AI prompt prefix

Paste this before any issue prompt:
> You are building the Fleet Control app described in the attached specification book. Follow sections 1 to 8 exactly (stack, conventions, data model, API surface, workflow). Implement only the Jira issue I name, nothing from later sprints. Filter every query by company. Write tests. Give me the file list, the code, the commands to run, and the commit messages (each starting with the Jira key).

---

# SPRINT 1: "Operators can see their robots"
**Nov 11 to Nov 24 · 16 points · Order: SCRUM-21 → SCRUM-20 → SCRUM-22 → SCRUM-23**

Sprint 1 checklist (Jira): close the empty "SCRUM Sprint 0", confirm Sprint 1 holds SCRUM-21, 20, 22, 23 (16 points), click **Start sprint**.

---

## SCRUM-21 · Set up repo, CI, and database (Task, 3 pts)

| | |
|---|---|
| **Goal** | A working repo with a FastAPI skeleton, a React skeleton, PostgreSQL in Docker, the first migration, and CI on every pull request. |
| **Depends on** | nothing |
| **Branch** | `feature/SCRUM-21-setup-repo-ci` |
| **Commit prefix** | `SCRUM-21 ...` |
| **PR title** | `SCRUM-21 Set up repo, CI, and database` |

**Jira steps:** move to In Progress. Add the repo to the GitHub for Jira connection (section 3) **before** the first push.

**Build steps**
1. On GitHub, create `fleet-control` under `ameen-pies` (private is fine). Add teammates under Settings → Collaborators. Clone it. Create the folder layout from section 2. Add a `.gitignore` (Python, Node, `.env`, `ml/data/`, `ml/models/`).
2. Create `.env.example` (section 4) and copy it to `.env`.
3. Create `docker-compose.yml` at the repo root:
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: fleet
      POSTGRES_PASSWORD: fleet
      POSTGRES_DB: fleet
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fleet"]
      interval: 5s
      timeout: 5s
      retries: 10
volumes:
  pgdata:
```
   Run `docker compose up -d db`, then create the test database: `docker compose exec db createdb -U fleet fleet_test`.
4. Backend: create a virtualenv in `backend/`. `requirements.txt` contains: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pydantic-settings`, `pyjwt`, `bcrypt`, `email-validator`, `python-multipart`, `pytest`, `httpx`. Install, then pin the versions that were installed.
5. `app/core/config.py`: a `Settings` class (pydantic-settings) reading `.env` for every variable in section 4.
6. `app/db/session.py`: engine from `DATABASE_URL`, `SessionLocal`, and a `get_db()` dependency. `app/db/base.py`: the declarative `Base`.
7. `app/main.py`: create the FastAPI app, add CORS using `CORS_ORIGINS`, and include a router at `/api/v1`. Add `GET /api/v1/health` returning `{"status": "ok", "database": "up"}`; it runs `SELECT 1`. If the query fails, return `503` with `{"status": "error", "database": "down"}`.
8. **Schema design:** create the SQLAlchemy models for `companies`, `users`, `robots` exactly as in section 5. Initialise Alembic (`alembic init alembic`), point `env.py` to `DATABASE_URL` and `Base.metadata`, generate the first migration, and run `alembic upgrade head`. Write `docs/data-model.md` containing a Mermaid `erDiagram` of these tables (extend it in later sprints).
9. Tests: `tests/conftest.py` creates a test engine on `TEST_DATABASE_URL`, runs migrations once, and provides a `client` fixture. `tests/test_health.py` asserts `200` and `database == "up"`.
10. Frontend: `npm create vite@latest frontend -- --template react-ts`. Install `react-router-dom`, `@tanstack/react-query`, Tailwind (follow the Tailwind + Vite guide). In `vite.config.ts` proxy `/api` to `http://localhost:8000`. Show a simple page that calls `/api/v1/health` and prints the result. Make sure `npm run lint` and `npm run build` pass.
11. CI: create `.github/workflows/ci.yml`:
```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: fleet
          POSTGRES_PASSWORD: fleet
          POSTGRES_DB: fleet_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U fleet"
          --health-interval 5s --health-timeout 5s --health-retries 10
    env:
      DATABASE_URL: postgresql+psycopg://fleet:fleet@localhost:5432/fleet_test
      TEST_DATABASE_URL: postgresql+psycopg://fleet:fleet@localhost:5432/fleet_test
      SECRET_KEY: ci-secret
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: backend/requirements.txt
      - run: pip install -r requirements.txt
      - run: alembic upgrade head
      - run: pytest -q
  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npm run build
```
12. Add `.github/pull_request_template.md` (section 3). Write the README: prerequisites, `docker compose up -d db`, backend run command (`uvicorn app.main:app --reload`), frontend run command (`npm run dev`), how to run tests.
13. Commit in small steps (`SCRUM-21 add docker compose`, `SCRUM-21 add fastapi skeleton and health endpoint`, ...), push, open the PR.

**Done when (from Jira)**
- [ ] The GitHub repo exists and every team member has access
- [ ] A CI pipeline runs on every pull request (the PR shows the CI check)
- [ ] The database is created and reachable from the app (`/api/v1/health` returns `database: up`)

**AI prompt:** "Implement SCRUM-21 from the book: repo layout, docker-compose with Postgres, FastAPI skeleton with the health endpoint, SQLAlchemy models + first Alembic migration for companies/users/robots, pytest setup, Vite React TS skeleton with Tailwind and proxy, and the CI workflow. Output every file."

---

## SCRUM-20 · Log in with roles (Story, 5 pts)

> As an operator, I want to log in with my account so that I only see the robots of my company.

| | |
|---|---|
| **Depends on** | SCRUM-21 merged |
| **Branch** | `feature/SCRUM-20-login-roles` |
| **PR title** | `SCRUM-20 Log in with roles` |

**Build steps (backend)**
1. `core/security.py`: `hash_password`, `verify_password` (bcrypt), `create_access_token(user)` (PyJWT, HS256, claims `sub` = user id, `role`, `company_id`, `exp`), `decode_token`.
2. `core/deps.py`: `get_current_user` (reads `Authorization: Bearer`, loads the user, `401` if missing/invalid/expired) and `require_admin` (`403` if role is not `admin`).
3. Router `auth`: 
   - `POST /api/v1/auth/login` with JSON `{email, password}` → `200 {access_token, token_type: "bearer", user: {id, email, full_name, role, company_id}}`. Wrong email or password → `401 {"detail": "Invalid email or password"}` (same message for both).
   - `GET /api/v1/auth/me` → the current user.
4. Router `admin`: `GET /api/v1/admin/ping` → `{"ok": true}`, protected by `require_admin`. (It exists only to prove the role check.)
5. `scripts/seed_users.py` (idempotent): creates the two companies and users from section 7, using the seed passwords from `.env`.

**Build steps (frontend)**
6. `api/client.ts`: fetch wrapper adding the token; on `401` clear the session and go to `/login`.
7. `auth/AuthContext.tsx`: holds `user` and `token` (persist the token in `localStorage`), exposes `login()` and `logout()`, and loads `/auth/me` on startup.
8. `ProtectedRoute`: redirects to `/login` if logged out. `RoleRoute role="admin"`: shows a "Not allowed" page to operators.
9. `LoginPage`: email + password form, shows the error message on failure, redirects to `/robots` on success.
10. `Layout`: navbar with the app name, the user's name and role, a **Logout** button, and links. Links for admin-only pages (e.g. "Register robot", added in SCRUM-22) are hidden for operators.

**Tests**
- Login with correct credentials returns a token. Wrong password returns `401`.
- `/auth/me` without a token returns `401`. With a token returns the right user.
- `/admin/ping` returns `200` for admin, `403` for operator, `401` without token.

**Acceptance checklist**
- [ ] A user can log in with email and password
- [ ] A wrong password shows an error message
- [ ] An admin can see the admin pages, an operator cannot
- [ ] A logged-out user is redirected to the login page

**AI prompt:** "Implement SCRUM-20: JWT login, /auth/me, role dependencies, admin ping endpoint, seed script, and the React login page, auth context, protected and role routes, and navbar. Include pytest tests."

---

## SCRUM-22 · Register a robot to the fleet (Story, 3 pts)

> As an admin, I want to register a robot with its name and serial number so that it becomes part of my fleet.

| | |
|---|---|
| **Depends on** | SCRUM-20 |
| **Branch** | `feature/SCRUM-22-register-robot` |
| **PR title** | `SCRUM-22 Register a robot to the fleet` |

**Build steps (backend)**
1. Schema `RobotCreate`: `name` (1 to 100 chars), `serial_number` (3 to 50 chars, letters, digits, `-`, `_`).
2. `POST /api/v1/robots` (admin only): 
   - Generate `api_key = secrets.token_urlsafe(32)`. Store `api_key_hash = sha256(api_key)` and `api_key_prefix = api_key[:8]`. **Never store the plain key.**
   - Create the robot in the admin's company.
   - Response `201 {id, name, serial_number, created_at, api_key}`. This is the **only** time `api_key` is returned.
   - Duplicate serial number (checked globally) → `409 {"detail": "A robot with this serial number already exists"}`. Catch the unique-constraint error too, in case of a race.
3. Operators get `403`.

**Build steps (frontend)**
4. Page `/robots/new` (wrapped in `RoleRoute role="admin"`): form with name and serial number, client-side validation, shows the server error message on `409`.
5. On success show a **"Robot registered"** screen with the API key in a read-only box, a **Copy** button, and the warning "Save this key now. It will not be shown again." Then a link back to `/robots`.
6. Invalidate the robots query so the new robot appears in the list right away.

**Tests**
- Admin creates a robot → `201`, key present, DB stores only the hash.
- Duplicate serial → `409`. Operator → `403`. Invalid serial → `422`.
- The robot is created in the admin's company, not another.

**Acceptance checklist**
- [ ] The form requires a name and a unique serial number
- [ ] A duplicate serial number is rejected with a clear message
- [ ] The new robot appears in the fleet right after saving

**AI prompt:** "Implement SCRUM-22: admin-only POST /robots with hashed API key returned once, 409 on duplicate serial, and the React register page with the one-time key screen. Include tests."

---

## SCRUM-23 · Robot list page (Story, 5 pts)

> As an operator, I want to see a list of all my robots so that I can check my fleet at a glance.

| | |
|---|---|
| **Depends on** | SCRUM-22 |
| **Branch** | `feature/SCRUM-23-robot-list` |
| **PR title** | `SCRUM-23 Robot list page` |

**Build steps (backend)**
1. `services/robot_status.py`: `compute_status(robot, latest_telemetry, now)`. **In this sprint it is a stub that always returns `"offline"`** (there is no telemetry yet). SCRUM-27 replaces it with the real rule. Keep the function signature stable.
2. `GET /api/v1/robots?search=` (any logged-in user): returns robots of the **current user's company only**, filtered by `name ILIKE %search%` when `search` is given, ordered by name. Item shape: `{id, name, serial_number, status, last_seen}` (`last_seen` is `null` for now).

**Build steps (frontend)**
3. Page `/robots` (default page after login): a table with columns Name, Serial number, Status.
4. `StatusBadge` component (green `active`, grey `idle`, red `offline`).
5. Search input with a 300 ms debounce that re-queries with `?search=`.
6. Empty state ("No robots yet") and loading/error states. Admins also see a **Register robot** button linking to `/robots/new`.

**Tests**
- Two companies, each with robots: user A never sees B's robots.
- Search is case-insensitive and partial. Empty search returns all.
- Unauthenticated request returns `401`.

**Acceptance checklist**
- [ ] The list shows name, serial number, and current status
- [ ] I can search robots by name
- [ ] I only see robots belonging to my company

**AI prompt:** "Implement SCRUM-23: company-scoped GET /robots with name search and a stub compute_status that returns offline, plus the React robots table with debounced search, status badge, empty state and admin register button. Include tests for company isolation."

---

## Sprint 1 review
- [ ] All 4 issues Done and visible with branch/PR in Jira
- [ ] `docker compose up -d db` + backend + frontend run from the README only
- [ ] Demo: log in as admin → register a robot → see it in the list → log in as operator → no admin links
- [ ] Complete the sprint. Write down the points finished.

---

# SPRINT 2: "A robot is visible live"
**Nov 25 to Dec 8 · 16 points · Order: SCRUM-24 → SCRUM-25 → SCRUM-26 → SCRUM-27**

Sprint 2 checklist (Jira): complete Sprint 1, then **Start sprint** on "SCRUM Sprint 2" (goal: "A robot is visible live"). Confirm 16 points.

---

## SCRUM-24 · Set up telemetry storage (Task, 3 pts)

| | |
|---|---|
| **Goal** | A `telemetry` table and data-access functions that can take at least 1 record per second per robot. |
| **Depends on** | Sprint 1 merged |
| **Branch** | `feature/SCRUM-24-telemetry-storage` |
| **PR title** | `SCRUM-24 Set up telemetry storage` |

**Build steps**
1. Model `Telemetry` and migration exactly as in section 5, including the index `(robot_id, ts DESC)`. `battery_pct` has a check constraint `0 to 100`.
2. `services/telemetry_repo.py` (plain functions, no HTTP):
   - `insert_telemetry(db, robot_id, ts, lat, lng, battery_pct, status)`
   - `get_latest(db, robot_id)` → the newest row or `None`
   - `get_latest_for_company(db, company_id)` → one latest row per robot, using `SELECT DISTINCT ON (robot_id) ... ORDER BY robot_id, ts DESC`
3. `scripts/telemetry_load_test.py`: creates 5 temporary robots, inserts 1 record per second per robot for 60 seconds (use threads or asyncio, each with its own session), then prints total inserted and the p95 insert time. Clean up afterwards.
4. Update `docs/data-model.md` with the telemetry table.

**Tests:** insert then read back; `get_latest` returns the most recent by `ts`; `get_latest_for_company` returns exactly one row per robot and ignores other companies; a battery of `101` is rejected.

**Done when (from Jira)**
- [ ] A table exists for position, battery, status, and timestamp
- [ ] A query can return the latest data of one robot
- [ ] It handles at least 1 record per second per robot in a test (the load test shows 300 or more inserts in 60 s and no errors)

**AI prompt:** "Implement SCRUM-24: Telemetry model + Alembic migration with the index, the repo functions including DISTINCT ON, a load-test script for 5 robots at 1 Hz for 60 s, and pytest tests."

---

## SCRUM-25 · Receive robot telemetry through an API (Story, 5 pts)

> As an operator, I want the platform to receive data from my robots so that I always work with up-to-date information.

| | |
|---|---|
| **Depends on** | SCRUM-24 |
| **Branch** | `feature/SCRUM-25-telemetry-api` |
| **PR title** | `SCRUM-25 Receive robot telemetry through an API` |

**API contract:** `POST /api/v1/robot/telemetry`
- Header: `X-Robot-Key: <api key>`
- Body: `{"lat": 35.8256, "lng": 10.6369, "battery_pct": 87.5, "status": "active", "ts": "2026-11-26T10:00:00Z"}` (`ts` optional, defaults to server time)
- Validation: `lat` -90..90, `lng` -180..180, `battery_pct` 0..100, `status` in `active`/`idle`.
- `201 {"ok": true}` on success. Unknown or missing key → `401 {"detail": "Invalid robot key"}`. Bad data → `422` with a clear message. The service must never crash on bad input.

**Build steps**
1. `core/deps.py`: `get_current_robot` reads `X-Robot-Key`, hashes it (SHA-256), looks up `robots.api_key_hash`, returns the robot or raises `401`.
2. Router `robot_api` with the endpoint above. Store `received_at = now()`.
3. **Robot simulator**, `scripts/simulator.py`:
   - CLI: `python -m scripts.simulator --api-url http://localhost:8000 --key <KEY> [--key <KEY2> ...] --interval 2`
   - Each simulated robot starts near Sousse (about `35.8256, 10.6369`), moves in a small random walk, drains battery by about 0.02 % per tick, and randomly alternates `active`/`idle`.
   - Prints one line per request and handles connection errors by retrying.
   - It will be extended in SCRUM-29 (follow routes) and SCRUM-31 (send alerts).
4. README: how to register a robot in the UI, copy its key, and run the simulator.

**Tests:** valid key → `201` and a row stored with the right `robot_id`; unknown key → `401`; no header → `401`; battery `150` → `422`; missing `lat` → `422`; two robots' data never mix.

**Acceptance checklist**
- [ ] A robot can send position, battery level, and status to the API
- [ ] Requests from unregistered robots are rejected
- [ ] Received data is stored with a timestamp
- [ ] Invalid data returns a clear error without crashing the service

**AI prompt:** "Implement SCRUM-25: X-Robot-Key auth dependency, POST /robot/telemetry with validation, and the scripts/simulator.py multi-robot simulator. Include tests for 401, 422 and data isolation."

---

## SCRUM-26 · Show robot position on a live map (Story, 5 pts)

> As an operator, I want to see where each robot is on a map so that I know where my fleet is at any moment.

| | |
|---|---|
| **Depends on** | SCRUM-25 |
| **Branch** | `feature/SCRUM-26-live-map` |
| **PR title** | `SCRUM-26 Show robot position on a live map` |

**Build steps (backend)**
1. `GET /api/v1/robots/latest` (user): for the current company, one item per robot: `{id, name, serial_number, lat, lng, battery_pct, status, last_seen}`. Robots with no telemetry have `lat`/`lng` = `null`. Uses `get_latest_for_company`. (Status uses `compute_status`; the real rule arrives in SCRUM-27.)

**Build steps (frontend)**
2. Install `react-leaflet` and `leaflet`. Import `leaflet/dist/leaflet.css`. Fix the default marker icon paths (known Leaflet + bundler issue).
3. Page `/map` (add it to the navbar): full-height map with OpenStreetMap tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`) and the required attribution.
4. One marker per robot that has a position. Popup shows the robot's name and status.
5. Poll the endpoint every **5 seconds** (`refetchInterval: 5000`) so markers move. Fit the map to all markers on first load only (do not re-zoom on every refresh).
6. Show a small note when no robot has sent data yet.

**Tests (backend):** returns only the company's robots; returns the newest position per robot; robot without data has null coordinates.

**Acceptance checklist**
- [ ] Each registered robot appears as a marker on the map
- [ ] The position updates at least every 10 seconds (run the simulator and watch the marker move)
- [ ] Clicking a marker shows the robot's name and status

**AI prompt:** "Implement SCRUM-26: GET /robots/latest scoped by company, and a React-Leaflet map page polling every 5 seconds with a popup showing name and status. Fit bounds only on first load."

---

## SCRUM-27 · Battery and status panel (Story, 3 pts)

> As an operator, I want to see each robot's battery level and status so that I can tell when it needs charging or attention.

| | |
|---|---|
| **Depends on** | SCRUM-26 |
| **Branch** | `feature/SCRUM-27-battery-status-panel` |
| **PR title** | `SCRUM-27 Battery and status panel` |

**Status rule (replace the stub in `services/robot_status.py`)**
- No telemetry, or latest telemetry older than **60 seconds** → `offline`.
- Otherwise the status of the latest telemetry (`active` or `idle`).
- `compute_status` takes `now` as a parameter so tests can control time.

**Build steps**
1. Implement the rule. Make `GET /robots` (SCRUM-23) and `GET /robots/latest` both use it. Add `battery_pct` and `last_seen` to the `GET /robots` items.
2. Frontend `BatteryBadge`: shows the percentage with a bar. **Under 20 % is red**, 20 to 50 % amber, above 50 % green. Offline robots show "unknown" instead of a stale battery value.
3. Frontend `StatusPanel`: a side panel on the map page listing every robot with its status badge and battery badge, refreshed with the map (5 s). Clicking a row centers the map on that robot.
4. Reuse `BatteryBadge` in the robots table (SCRUM-23 page).

**Tests:** robot with telemetry 59 s old → active; 61 s old → offline; no telemetry → offline; battery color thresholds (19 red, 20 amber, 51 green).

**Acceptance checklist**
- [ ] The panel shows battery percentage and status (active, idle, offline)
- [ ] A battery under 20 % is highlighted in red
- [ ] A robot with no data for 1 minute shows as offline (stop the simulator and wait one minute)

**AI prompt:** "Implement SCRUM-27: replace compute_status with the 60-second offline rule, update both robot endpoints, and add BatteryBadge and StatusPanel components with the red under-20% rule. Include time-controlled tests."

---

## Sprint 2 review
- [ ] All 4 issues Done with branch/PR in Jira
- [ ] Demo: register 2 robots → run the simulator → both move on the map → stop one → it turns offline after a minute
- [ ] Complete the sprint and note the points finished

---

# SPRINT 3: "Missions and alerts work"
**Dec 9 to Dec 22 · 15 points · Order: SCRUM-28 → SCRUM-29 → SCRUM-30 → SCRUM-31 → SCRUM-32**

Sprint 3 checklist (Jira): complete Sprint 2, **Start sprint** on "SCRUM Sprint 3". Confirm 15 points.

---

## SCRUM-28 · Define the mission data model (Task, 2 pts)

| | |
|---|---|
| **Goal** | Tables for routes, waypoints, missions, and mission events, plus seeded demo routes. |
| **Depends on** | Sprint 2 merged |
| **Branch** | `feature/SCRUM-28-mission-data-model` |
| **PR title** | `SCRUM-28 Define the mission data model` |

**Build steps**
1. Models and one migration for `routes`, `waypoints`, `missions`, `mission_events` exactly as in section 5. Add a check constraint on `missions.status` and `mission_events.action`, and a unique constraint on `(route_id, seq)`.
2. Allowed status transitions (write them in `docs/data-model.md`): `scheduled → running → completed | stopped`, and `scheduled → cancelled`. Nothing leaves `completed`, `stopped`, or `cancelled`.
3. `scripts/seed_routes.py` (idempotent): creates 2 routes for "Demo Security SA" ("North perimeter", "Main gate loop"), each with 5 to 6 waypoints around Sousse (`35.8256, 10.6369` ± about 0.002°).
4. Update the Mermaid ER diagram in `docs/data-model.md` with all mission tables.

**Tests:** migration applies and rolls back cleanly (`alembic downgrade -1`); creating a mission links a robot, a route, and a start time; invalid status is rejected by the database.

**Done when (from Jira)**
- [ ] Tables exist for routes, waypoints, and missions with a status
- [ ] A mission links a robot to a route and a start time
- [ ] The model is documented in the repo

**AI prompt:** "Implement SCRUM-28: models and migration for routes, waypoints, missions, mission_events with constraints, the seed_routes script, and the updated data-model doc with a Mermaid ER diagram."

---

## SCRUM-29 · Start and stop a mission remotely (Story, 3 pts)

> As an operator, I want to start or stop a patrol manually so that I can react to unexpected situations.

| | |
|---|---|
| **Depends on** | SCRUM-28 |
| **Branch** | `feature/SCRUM-29-start-stop-mission` |
| **PR title** | `SCRUM-29 Start and stop a mission remotely` |

**Scope note:** since the backlog has no "create route/mission" story, this issue includes **creating a mission from a seeded route**, then starting and stopping it. Mention it in a Jira comment.

**API contract**
- `GET /api/v1/routes` → company routes with their waypoints.
- `POST /api/v1/missions` `{robot_id, route_id}` → `201` mission with status `scheduled` (`scheduled_at = now`). Robot and route must belong to the user's company, else `404`.
- `GET /api/v1/missions` → company missions, newest first, each with robot name, route name, status, and its events.
- `POST /api/v1/missions/{id}/start` → status `running`, `started_at = now`, adds a `mission_events` row (`action=start`, `user_id`, `ts`). Only from `scheduled`. A robot can have only **one running mission**: otherwise `409 {"detail": "This robot already has a running mission"}`.
- `POST /api/v1/missions/{id}/stop` → status `stopped`, `ended_at = now`, adds a `mission_events` row (`action=stop`). Only from `running`, else `409`.
- Robot side: `GET /api/v1/robot/mission` (header `X-Robot-Key`) → `{"mission": null}` or `{"mission": {"id", "route": {"waypoints": [{seq, lat, lng}, ...]}}}` for the robot's running mission.

**Build steps**
1. `services/missions.py` with the state machine (one function per transition, raises a domain error mapped to `409`).
2. Routers as above. All queries filtered by company.
3. Simulator: every few ticks call `GET /robot/mission`. If a mission is running, move toward the next waypoint instead of random-walking and report `active`; when no mission, hold position and report `idle`. When the last waypoint is reached, call nothing (an operator stops it; auto-complete is a future improvement).
4. Frontend page `/missions` (add to navbar): a form with a robot dropdown and a route dropdown plus **Create mission**; a table of missions with status badges and **Start** (shown when `scheduled`) and **Stop** (shown when `running`) buttons; an expandable row listing the mission's events (action, user, time). Show the `409` message in a toast or inline.

**Tests:** full lifecycle scheduled → running → stopped with events recorded; start twice → `409`; second running mission on the same robot → `409`; stop a non-running mission → `409`; another company's robot or route → `404`; robot endpoint returns the running mission only for its own robot.

**Acceptance checklist**
- [ ] A Start button launches the selected mission
- [ ] A Stop button halts the robot and marks the mission as stopped (the simulated robot stops following the route)
- [ ] Both actions are recorded with the time and the user who did them

**AI prompt:** "Implement SCRUM-29: routes list, mission create/list/start/stop with the state machine and event logging, the robot mission endpoint, simulator route following, and the React missions page with Start/Stop buttons and event history. Include lifecycle tests."

---

## SCRUM-30 · Set up the email sending service (Task, 2 pts)

| | |
|---|---|
| **Goal** | The app can send emails reliably, safely configured, with failures logged. |
| **Depends on** | Sprint 2 merged (independent of SCRUM-28/29) |
| **Branch** | `feature/SCRUM-30-email-service` |
| **PR title** | `SCRUM-30 Set up the email sending service` |

**Build steps**
1. Add **Mailpit** to `docker-compose.yml` (dev mail catcher):
```yaml
  mailpit:
    image: axllent/mailpit
    ports: ["1025:1025", "8025:8025"]
```
   Run it. Sent emails appear at `http://localhost:8025`.
2. `services/email.py`: `send_email(to: str, subject: str, body: str) -> bool` using Python's `smtplib` and `email.message.EmailMessage`, with settings from `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`. Use TLS login only when `SMTP_USER` is set.
3. **Credentials come from environment variables only.** No secret in the code or in git.
4. On any exception: `logging.exception(...)`, return `False`, **never raise** (an email failure must never break the caller).
5. `scripts/send_test_email.py <recipient>` to send a test message.
6. README: how to point to a real provider by changing the env vars.

**Tests:** with `smtplib.SMTP` monkeypatched, a successful send returns `True` and builds the right message; a raised `SMTPException` returns `False` and logs an error.

**Done when (from Jira)**
- [ ] The app can send a test email through the chosen provider (visible in Mailpit)
- [ ] Credentials are stored as environment variables, not in the code
- [ ] A failed send is logged

**AI prompt:** "Implement SCRUM-30: Mailpit in docker-compose, services/email.py with smtplib that never raises and logs failures, a send_test_email script, and tests with a mocked SMTP."

---

## SCRUM-31 · Trigger an alert on intrusion or obstacle (Story, 5 pts)

> As an operator, I want to be alerted when a robot detects an intrusion or an obstacle so that I can respond quickly.

| | |
|---|---|
| **Depends on** | SCRUM-25, SCRUM-30 |
| **Branch** | `feature/SCRUM-31-robot-alerts` |
| **PR title** | `SCRUM-31 Trigger an alert on intrusion or obstacle` |

**API contract**
- `POST /api/v1/robot/events` (header `X-Robot-Key`) body `{"type": "intrusion" | "obstacle", "lat": ..., "lng": ..., "ts": optional}` → `201 {"id": ...}` and creates an `alerts` row for the robot's company. Any other `type` → `422`.
- `GET /api/v1/alerts?status=open|all` (default `open`) → alerts with robot name, type, location, time, acknowledged state, newest first.
- `GET /api/v1/alerts/open-count` → `{"count": n}`.
- `POST /api/v1/alerts/{id}/acknowledge` → sets `acknowledged`, `acknowledged_by`, `acknowledged_at`. Already acknowledged → `200` unchanged (idempotent). Another company's alert → `404`.

**Build steps**
1. Model `Alert` + migration as in section 5 (with the index).
2. `services/alerts.py`: `create_alert(...)`. After the alert is saved, **try** to email every user of that company with `email_notifications = true`, using `send_email` from SCRUM-30. The subject is `[Fleet Control] <type> alert from <robot name>`; the body has robot, type, time, and a link `FRONTEND_URL/alerts`. Run it as a FastAPI background task so ingestion stays fast and never fails because of email. (The per-user on/off toggle is not in the backlog; the column exists, default true.)
3. Routers as above.
4. Simulator: add `--events`. While running, each tick has a small chance (about 3 % obstacle, 1 % intrusion) to call `POST /robot/events` at the robot's current position.
5. Frontend page `/alerts` (the alerts dashboard): a table with robot, type badge (intrusion red, obstacle orange), location, time, and an **Acknowledge** button; a filter between open and all; polling every 10 s.
6. Navbar: a badge on "Alerts" showing the open count (poll `/alerts/open-count` every 10 s).

**Tests:** event creates an alert in the right company; invalid type → `422`; unknown key → `401`; acknowledge sets who and when; acknowledging twice is safe; `open-count` ignores acknowledged and other companies' alerts; email function is called for opted-in users and a failing email does not break the request (mock `send_email`).

**Acceptance checklist**
- [ ] A robot event of type intrusion or obstacle creates an alert
- [ ] The alert appears on the dashboard with robot, type, and time
- [ ] I can mark an alert as acknowledged

**AI prompt:** "Implement SCRUM-31: Alert model and migration, robot events endpoint, alerts list/count/acknowledge endpoints, best-effort email notification as a background task using services/email.py, simulator --events flag, and the React alerts page plus navbar badge. Include tests."

---

## SCRUM-32 · Write the statistics queries (Task, 3 pts)

| | |
|---|---|
| **Goal** | Fast, tested SQL queries behind the analytics charts, plus realistic demo data. |
| **Depends on** | SCRUM-24, SCRUM-29 |
| **Branch** | `feature/SCRUM-32-statistics-queries` |
| **PR title** | `SCRUM-32 Write the statistics queries` |

**Build steps**
1. `app/analytics/queries.py` (functions take a session and return plain Python data; no HTTP):
   - `missions_per_day(db, company_id, days=7, end_date=None)` → `[{"date": "2026-12-01", "completed": 3, "stopped": 1}, ...]`, one entry **for each day, including days with zero** (use `generate_series`). Counts missions by `ended_at` date and final status.
   - `battery_history(db, robot_id, hours=24, bucket_minutes=10)` → `[{"ts": ..., "avg_battery": ...}]` (bucketed average using `date_bin` or `date_trunc` arithmetic).
   - `uptime_pct(db, robot_id, days=7)` → percentage of 1-minute buckets in the window that contain at least one telemetry record, capped at 100.
2. `scripts/seed_demo_data.py`: generates 7 days of telemetry for 5 robots at one sample every 10 s (about 300,000 rows, use bulk insert or `COPY`), plus about 40 missions with mixed `completed`/`stopped` statuses and some alerts across the week. Make it idempotent or add a `--reset` flag.
3. Add or adjust indexes if a query is slow. Run `EXPLAIN ANALYZE` on each query and paste the key lines in `docs/data-model.md` under "Performance".
4. Benchmark test (mark with `@pytest.mark.slow`): on the seeded data each query runs in **under 2 seconds**.

**Tests:** `missions_per_day` returns exactly 7 entries and zero-fills empty days; counts match a hand-made small dataset; `uptime_pct` is `100` for continuous data, about `50` for half the window, `0` for none.

**Done when (from Jira)**
- [ ] A query returns missions per day for the last 7 days
- [ ] A query returns battery history and uptime per robot
- [ ] Each query runs in under 2 seconds on test data

**AI prompt:** "Implement SCRUM-32: the three analytics query functions in SQL with zero-filled days, a seed_demo_data script producing about 300k telemetry rows, EXPLAIN notes, and tests including a 2-second benchmark."

---

## Sprint 3 review
- [ ] All 5 issues Done with branch/PR in Jira
- [ ] Demo: create a mission → start → robot follows the route → stop; simulator with `--events` raises alerts → badge appears → acknowledge → email visible in Mailpit
- [ ] Complete the sprint, note the points finished, decide if Sprint 4 needs trimming (it runs over the holidays)

---

# SPRINT 4: "Analytics and incident prediction"
**Dec 23 to Jan 5 · 16 points · Order: SCRUM-33 → SCRUM-35 → SCRUM-36 → SCRUM-37**

Sprint 4 checklist (Jira): complete Sprint 3, **Start sprint** on "SCRUM Sprint 4". Confirm 16 points. The sprint covers the holidays; if needed, edit its dates or move SCRUM-37 to a fifth sprint.

---

## SCRUM-33 · Weekly patrol summary chart (Story, 3 pts)

> As a security manager, I want a weekly summary of patrols so that I can see how well my fleet is covering the site.

| | |
|---|---|
| **Depends on** | SCRUM-32 |
| **Branch** | `feature/SCRUM-33-weekly-summary-chart` |
| **PR title** | `SCRUM-33 Weekly patrol summary chart` |

**API contract:** `GET /api/v1/analytics/missions/weekly?week_offset=0` (user)
- `week_offset=0` is the **last 7 days ending today**; `1` is the 7 days before that; and so on. Must be an integer between 0 and 52, else `422`.
- Response: `{"from": "2026-12-23", "to": "2026-12-29", "days": [{"date": "2026-12-23", "completed": 2, "stopped": 1}, ...7 items]}`.
- Uses `missions_per_day` from SCRUM-32 with the company of the current user.

**Build steps**
1. Router `analytics` and the endpoint above, scoped by company.
2. Frontend page `/analytics` (add it to the navbar): a Recharts **stacked `BarChart`**, one bar per day, with **completed in green and stopped in red**, a legend, axis labels, and a tooltip.
3. **Previous week** and **Next week** buttons that change `week_offset` (Next is disabled at 0). Show the date range above the chart.
4. Empty state when the whole week has no missions ("No missions this week") while still showing the 7 days.

**Tests:** 7 days returned; `week_offset=1` returns the previous window; counts match a known dataset; another company's missions never appear; `week_offset=-1` → `422`.

**Acceptance checklist**
- [ ] The chart shows the number of missions per day for the last 7 days
- [ ] Completed and stopped missions are shown in different colors
- [ ] I can switch to the previous week

**AI prompt:** "Implement SCRUM-33: the weekly missions endpoint using the existing missions_per_day query, and a React analytics page with a Recharts stacked bar chart (completed green, stopped red) and previous/next week buttons."

---

## SCRUM-35 · Prepare the incident dataset (Task, 3 pts)

| | |
|---|---|
| **Goal** | A clean hourly dataset of incidents that a model can learn from, built from real alerts plus synthetic data when real data is too small. |
| **Depends on** | SCRUM-31 (alerts exist) |
| **Branch** | `feature/SCRUM-35-incident-dataset` |
| **PR title** | `SCRUM-35 Prepare the incident dataset` |

**Setup:** create `ml/` with its own `requirements.txt` (`pandas`, `numpy`, `scikit-learn`, `joblib`, `sqlalchemy`, `psycopg[binary]`, `matplotlib`). `ml/data/` and `ml/models/` stay out of git.

**Build steps**
1. `ml/export_incidents.py`: reads the `alerts` table (all companies or `--company-id`) and writes `ml/data/raw_incidents.csv` with columns `robot_id, type, ts, lat, lng, source` (`source = "real"`).
2. `ml/generate_fake_incidents.py --days 180 --seed 42`: creates synthetic incidents in `ml/data/fake_incidents.csv` (`source = "synthetic"`). Draw the number of incidents each hour from a Poisson distribution whose rate depends on the time: low base rate in the day (about 0.05), **higher at night 22:00 to 05:00 (about 0.4)**, a bit higher on weekends. Random type (70 % obstacle, 30 % intrusion), random robot id from 1 to 5, coordinates near Sousse. Fixing the seed makes it reproducible.
3. `ml/clean.py`: load real + synthetic, parse timestamps as UTC, **drop exact duplicates** (same robot, type, and timestamp within 1 second), drop rows with missing timestamps, invalid types, or coordinates out of range. Print how many rows each rule removed.
4. `ml/build_dataset.py`: floor timestamps to the hour, build a **complete hourly grid** (every hour in the range, including hours with zero incidents) and write `ml/data/hourly_dataset.csv` with columns:
   `ts_hour, hour, dow (0=Mon), is_weekend, is_night, incident_count, incident (0/1)`.
5. `ml/README.md`: how to run steps 1 to 4 in order, what each column means, and a clear note: **the synthetic data is made up, so the model results only demonstrate the method, not real-world performance.** Say this in your report too.
6. Add a few tests in `ml/tests/` (pytest): the hourly grid has no gaps; duplicates are removed; `incident` equals `incident_count > 0`.

**Done when (from Jira)**
- [ ] Past alerts are exported with robot, type, location, and time
- [ ] Missing or duplicate records are cleaned
- [ ] Enough fake data exists to train on if real incidents are too few (at least 180 days of hourly rows, which is more than 4,000 rows)

**AI prompt:** "Implement SCRUM-35: the ml/ folder scripts export_incidents, generate_fake_incidents (Poisson, higher at night and weekends, seeded), clean, build_dataset (complete hourly grid with incident flag), the README with the synthetic-data caveat, and small tests."

---

## SCRUM-36 · Train the incident prediction model (Task, 5 pts)

| | |
|---|---|
| **Goal** | A trained, measured, documented model that predicts whether an incident occurs in a given hour. |
| **Depends on** | SCRUM-35 |
| **Branch** | `feature/SCRUM-36-train-incident-model` |
| **PR title** | `SCRUM-36 Train the incident prediction model` |

**Build steps**
1. `ml/train.py` loads `hourly_dataset.csv`.
2. **Features:** `hour_sin`, `hour_cos` (cyclic encoding of the hour), `dow` (one-hot or numeric), `is_weekend`, `is_night`. **Target:** `incident`. Use calendar features only, because the app must predict the next 24 hours where recent history is unknown.
3. **Time-based split:** the first 80 % of the rows in time order for training, the last 20 % for testing. **Never shuffle** (it would leak the future into training).
4. **Baselines:**
   - A: always predict the training-set incident rate.
   - B: the historical incident rate for each (day-of-week, hour) pair.
5. **Models:** `LogisticRegression` and `RandomForestClassifier` (200 trees, `class_weight="balanced"`).
6. **Metrics on the test set** for every baseline and model: accuracy, ROC-AUC, PR-AUC, F1, Brier score. Choose the decision threshold that maximizes F1 on a validation slice taken from the end of the training set (not on the test set). Remember **accuracy alone is misleading** when incidents are rare; judge mainly on PR-AUC and F1.
7. Pick the best model by PR-AUC. Save it with `joblib` to `ml/models/incident_model.joblib` and write `ml/models/metrics.json` containing `best_model`, `threshold`, the feature list, the metrics table, and the training date range.
8. Write `docs/ml-report.md`: dataset description, features, split, results table (baselines vs models), the chosen model and threshold, a feature-importance or coefficient plot saved to `docs/`, and the limitations (synthetic data, calendar-only features, no zone or weather information).
9. Tests (`ml/tests/`): training runs end-to-end on a tiny generated dataset; the saved model loads and `predict_proba` returns 24 values in `[0, 1]`; the split is chronological.

**Done when (from Jira)**
- [ ] Data is split into training and test sets
- [ ] A baseline model is trained and its accuracy is measured
- [ ] Results are documented in the repo

**AI prompt:** "Implement SCRUM-36: ml/train.py with a chronological 80/20 split, two baselines, logistic regression and random forest, metrics (accuracy, ROC-AUC, PR-AUC, F1, Brier), threshold chosen on a validation slice, saved joblib and metrics.json, and the docs/ml-report.md write-up with limitations."

---

## SCRUM-37 · See predicted high-risk time slots (Story, 5 pts)

> As a security manager, I want to see when incidents are most likely to happen so that I can schedule patrols at the right times.

| | |
|---|---|
| **Depends on** | SCRUM-36 (trained model file) |
| **Branch** | `feature/SCRUM-37-risk-prediction-page` |
| **PR title** | `SCRUM-37 See predicted high-risk time slots` |

**API contract:** `GET /api/v1/predictions/risk?hours=24` (user)
- `hours` between 1 and 72, default 24, else `422`.
- Response: `{"refreshed_at": "...", "threshold": 0.31, "slots": [{"ts": "2026-12-30T14:00:00Z", "probability": 0.12, "level": "low"}, ...]}` with one slot per hour, starting at the **next full hour**, in order.
- `level`: `high` when `probability >= threshold` (from `metrics.json`), `medium` when `probability >= 0.7 × threshold`, otherwise `low`.
- If the model file is missing → `503 {"detail": "Prediction model not available. Run ml/train.py."}`.

**Build steps**
1. `services/prediction.py`: load the model and `metrics.json` once at startup (path from an env var `MODEL_PATH`, default `ml/models/incident_model.joblib`). Build the feature rows for the next N hours **exactly as in training** (same feature names and order, same cyclic encoding). Call `predict_proba`.
2. **Refresh rule:** cache the result in memory and recompute when it is older than **60 minutes** or when `hours` changes. Return `refreshed_at`. This satisfies "refreshes at least once a day".
3. Router `predictions` with the endpoint above.
4. Frontend page `/predictions` (add to navbar): 
   - A row of hourly cells (or bars) for the next 24 hours, labeled with the local hour, **color by level** (high red, medium amber, low green), and a **"High risk"** label on high slots.
   - A summary sentence such as "3 high-risk slots in the next 24 hours: 02:00, 03:00, 23:00".
   - "Last updated" text from `refreshed_at` and a **Refresh** button that forces a refetch.
   - Loading, error, and "model not available" states.
5. Document in the README how to train (`python ml/train.py`) before using the page.

**Tests:** returns exactly 24 slots in ascending order starting after now; levels follow the threshold rule (use a small fake model in the test); cache returns the same `refreshed_at` within 60 minutes; `hours=100` → `422`; missing model → `503`.

**Acceptance checklist**
- [ ] A page shows the predicted risk per hour for the next 24 hours
- [ ] High-risk slots are highlighted
- [ ] The prediction refreshes at least once a day

**AI prompt:** "Implement SCRUM-37: a prediction service that loads the joblib model and metrics.json, builds next-N-hour features identically to training, caches for 60 minutes, the GET /predictions/risk endpoint with levels from the threshold, and the React page with colored hourly slots, high-risk highlight, last-updated text and refresh button. Include tests with a fake model."

---

## Sprint 4 review and project wrap-up
- [ ] All 4 issues Done with branch/PR in Jira
- [ ] In Jira, move each finished **epic** (SCRUM-5, 6, 7, 8, 9, 34) to **Done**; check the **Timeline** tab and the **Summary** tab for the final picture
- [ ] Complete Sprint 4 and write the final velocity per sprint (16, 16, 15, 16 planned vs your actuals)
- [ ] Final demo script (10 minutes): login → register robot → live map with simulator → create and stop a mission → alert and acknowledge → weekly chart → prediction page
- [ ] README has screenshots, setup steps, architecture diagram, and the synthetic-data note
- [ ] Take screenshots of the Jira backlog, a completed sprint, the Timeline, and an issue's Development panel for your report

---

# APPENDIX

## A. Troubleshooting the GitHub ↔ Jira link

| Symptom | Fix |
|---|---|
| Development panel empty | Add the repo to the connected organization (GitHub for Jira → pencil icon). Make sure the key is uppercase and in the branch name, commit, or PR title. Push a new commit. Wait a few minutes. |
| Branch created before connecting | Rename it with the key and push, or open a PR with the key in the title. |
| Smart commit did nothing | Check the issue key and that the transition name exists in the space's workflow (To Do, In Progress, Done). If still failing, move the issue manually or use an Automation rule. |
| Issue key not recognized | Keys here are `SCRUM-<n>`, not `FLT-<n>`. |

## B. Useful JQL (Jira search → switch to JQL)
```
project = SCRUM AND sprint in openSprints()
project = SCRUM AND status != Done ORDER BY rank
project = SCRUM AND issuetype = Task
project = SCRUM AND development[branches].all > 0
project = SCRUM AND development[pullrequests].all > 0
project = SCRUM AND "parent" = SCRUM-6
```
If a `development[...]` clause is rejected, check the syntax for your Jira version.

## C. Commands cheat sheet

```bash
# start services
docker compose up -d db mailpit
# backend
cd backend && source .venv/bin/activate
alembic upgrade head
python -m scripts.seed_users
python -m scripts.seed_routes
uvicorn app.main:app --reload
pytest -q
# frontend
cd frontend && npm install && npm run dev
# simulator
cd backend && python -m scripts.simulator --api-url http://localhost:8000 --key <KEY> --events
# ML
cd ml && python export_incidents.py && python generate_fake_incidents.py --days 180 --seed 42
python clean.py && python build_dataset.py && python train.py
```

## D. Order of everything at a glance

```
S1  SCRUM-21 repo/CI/DB → SCRUM-20 login → SCRUM-22 register robot → SCRUM-23 robot list
S2  SCRUM-24 telemetry storage → SCRUM-25 telemetry API + simulator → SCRUM-26 live map → SCRUM-27 status panel
S3  SCRUM-28 mission model → SCRUM-29 start/stop mission → SCRUM-30 email → SCRUM-31 alerts → SCRUM-32 stats queries
S4  SCRUM-33 weekly chart → SCRUM-35 dataset → SCRUM-36 train model → SCRUM-37 risk page
```
