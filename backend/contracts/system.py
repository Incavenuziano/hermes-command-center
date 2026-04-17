from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ComponentStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class SystemComponent:
    name: str
    status: ComponentStatus
    detail: str | None = None
    latency_ms: int | None = None


@dataclass(slots=True)
class SystemHealth:
    overall_status: ComponentStatus
    runtime: SystemComponent
    database: SystemComponent
    event_bus: SystemComponent
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SystemDegradationStatus:
    component: str
    reason: str
    can_retry: bool = True


@dataclass(slots=True)
class SystemIdentity:
    service: str
    environment: str
    bind: str
    transport: str
    auth_mode: str
