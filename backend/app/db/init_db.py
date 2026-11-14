"""Create the SQLite schema.

There are no Alembic migrations in this adapted build: the models are the
single source of truth and ``create_all`` is idempotent, so starting the app
or running a seed script on a fresh machine is enough.
"""

from app.db.base import Base
from app.db.session import engine

# Importing the package registers every model on Base.metadata.
import app.models  # noqa: F401,E402


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database schema is up to date.")
