"""Health endpoint, used by CI and the operator shell."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness and database check", response_model=None)
def health(db: Session = Depends(get_db)) -> dict[str, str] | JSONResponse:
    """Return 200 when the database answers, 503 when it does not."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "down"},
        )

    return {"status": "ok", "database": "up"}
