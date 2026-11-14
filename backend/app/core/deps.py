"""Request dependencies: the current user, role checks, and the current robot."""

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token, hash_robot_key
from app.db.session import get_db
from app.models.robot import Robot
from app.models.user import User, UserRole

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Load the user from the ``Authorization: Bearer`` header."""
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise CREDENTIALS_ERROR

    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise CREDENTIALS_ERROR from None

    user = db.get(User, user_id)
    if user is None:
        raise CREDENTIALS_ERROR
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role is not UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user


def get_current_robot(
    x_robot_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Robot:
    """Resolve the robot from the SHA-256 hash of its ``X-Robot-Key`` header."""
    if not x_robot_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid robot key",
        )

    robot = db.scalar(
        select(Robot).where(Robot.api_key_hash == hash_robot_key(x_robot_key))
    )
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid robot key",
        )
    return robot
