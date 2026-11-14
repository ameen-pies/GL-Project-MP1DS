"""Enumerations shared by models and schemas."""

import enum


class TelemetryStatus(str, enum.Enum):
    ACTIVE = "active"
    IDLE = "idle"


class MissionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    CANCELLED = "cancelled"


class MissionAction(str, enum.Enum):
    START = "start"
    STOP = "stop"


class AlertType(str, enum.Enum):
    INTRUSION = "intrusion"
    OBSTACLE = "obstacle"
