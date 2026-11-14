# Data model

Fleet Control keeps one tenant boundary: every user, robot, route, mission, and
alert belongs to a `companies` row, and every query filters on the signed-in
user's `company_id`. Timestamps are stored in UTC and displayed in the
browser's local time.

This build uses SQLAlchemy models as the source of truth and creates the schema
with `Base.metadata.create_all` at startup (see `backend/app/db/init_db.py`).
There is no Alembic history in the adapted SQLite build; the models and this
document move together.

```mermaid
erDiagram
    companies ||--o{ users : "employs"
    companies ||--o{ robots : "owns"
    companies ||--o{ routes : "defines"
    companies ||--o{ missions : "schedules"
    companies ||--o{ alerts : "receives"

    users ||--o{ missions : "creates"
    users ||--o{ mission_events : "performs"
    users ||--o{ alerts : "acknowledges"

    robots ||--o{ telemetry : "reports"
    robots ||--o{ missions : "runs"
    robots ||--o{ alerts : "raises"

    routes ||--o{ waypoints : "has"
    routes ||--o{ missions : "is followed by"

    missions ||--o{ mission_events : "logs"

    companies {
        int id PK
        string name
        datetime created_at
    }

    users {
        int id PK
        int company_id FK
        string email UK
        string password_hash
        string full_name
        enum role "admin | operator"
        bool email_notifications
        datetime created_at
    }

    robots {
        int id PK
        int company_id FK
        string name
        string serial_number UK
        string api_key_hash
        string api_key_prefix
        datetime created_at
    }

    telemetry {
        bigint id PK
        int robot_id FK
        datetime ts
        float lat
        float lng
        float battery_pct "0..100"
        enum status "active | idle"
        datetime received_at
    }

    routes {
        int id PK
        int company_id FK
        string name
        datetime created_at
    }

    waypoints {
        int id PK
        int route_id FK
        int seq "unique per route"
        float lat
        float lng
    }

    missions {
        int id PK
        int company_id FK
        int robot_id FK
        int route_id FK
        enum status "scheduled | running | completed | stopped | cancelled"
        datetime scheduled_at
        datetime started_at
        datetime ended_at
        int created_by FK
        datetime created_at
    }

    mission_events {
        int id PK
        int mission_id FK
        enum action "start | stop"
        int user_id FK
        datetime ts
    }

    alerts {
        int id PK
        int company_id FK
        int robot_id FK
        enum type "intrusion | obstacle"
        float lat
        float lng
        datetime ts
        bool acknowledged
        int acknowledged_by FK
        datetime acknowledged_at
    }
```

## Mission state transitions

```
scheduled ──start──> running ──stop──> stopped
    │                   │
    │                   └──(auto-complete is a future improvement)
    └──cancel──> cancelled
```

- `start` is allowed only from `scheduled`, and only if the robot has no other
  running mission (`409`).
- `stop` is allowed only from `running` (`409` otherwise).
- Nothing leaves `completed`, `stopped`, or `cancelled`.
- Every successful `start`/`stop` appends a `mission_events` row with the user
  and the UTC timestamp.

## Indexes and constraints

| Table | Index / constraint | Purpose |
|---|---|---|
| `users` | unique `email` | login lookup and identity |
| `robots` | unique `serial_number`, `company_id` index | duplicate check, tenant scoping |
| `telemetry` | `(robot_id, ts)` index, check `0 <= battery_pct <= 100` | latest sample and history reads |
| `waypoints` | unique `(route_id, seq)` | stable route order |
| `missions` | check on `status`, `company_id` / `robot_id` indexes | valid states and scoping |
| `mission_events` | check on `action`, `mission_id` index | traceability |
| `alerts` | `(company_id, acknowledged, ts)` index | open queue and dashboard count |

## Performance

- `get_latest_for_company` uses a window function (`ROW_NUMBER() OVER PARTITION
  BY robot_id ORDER BY ts DESC`) instead of PostgreSQL-only `DISTINCT ON`, so
  the same query works on SQLite and PostgreSQL.
- `missions_per_day` groups by the date of `ended_at` and zero-fills the seven
  days in Python, so an empty day still appears in the response.
- `battery_history` and `uptime_pct` read the indexed `(robot_id, ts)` range and
  bucket in Python, because SQLite has no `date_bin`. This is comfortable at
  demo scale; on PostgreSQL the bucketing belongs in SQL.
- The demo seed (`backend/scripts/seed_demo_data.py`) writes seven days of
  telemetry at one sample per 10 seconds for five robots (about 300k rows) in
  bulk, and the analytics tests cover the query contracts.
