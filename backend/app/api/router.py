"""Versioned API router. Add one router per resource as sprints land."""

from fastapi import APIRouter

from app.api import alerts, analytics, auth, health, missions, predictions, robot_api, robots

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(robots.router)
api_router.include_router(robot_api.router)
api_router.include_router(missions.router)
api_router.include_router(alerts.router)
api_router.include_router(analytics.router)
api_router.include_router(predictions.router)
