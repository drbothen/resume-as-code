"""Output models for JSON response formatting."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

FORMAT_VERSION = "1.0.0"


class JSONResponse(BaseModel):
    """Standard JSON response format for all commands."""

    format_version: str = Field(default=FORMAT_VERSION)
    status: str  # "success" | "error" | "dry_run"
    command: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=2)
