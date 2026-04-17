from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ErrorEnvelope:
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None
