"""Unified Scope model for executive-level positions.

Captures leadership scale indicators: P&L, revenue, team size, budget, geography, customers.
Used by Position model. WorkUnit.scope is deprecated in favor of Position.scope.

This module consolidates the previously separate PositionScope and WorkUnit.Scope
models into a single source of truth.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Scope(BaseModel):
    """Unified scope model for executive-level positions.

    Captures leadership scale indicators: P&L, revenue, team size,
    budget, geography, customers. Used by Position and inherited
    by work units via position reference.

    All fields are optional - only populated fields render in scope line.
    """

    model_config = ConfigDict(extra="forbid")

    revenue: str | None = Field(
        default=None,
        description="Revenue impact, e.g., '$500M'",
    )
    team_size: int | None = Field(
        default=None,
        ge=0,
        description="Total team/org size",
    )
    direct_reports: int | None = Field(
        default=None,
        ge=0,
        description="Direct reports count",
    )
    budget: str | None = Field(
        default=None,
        description="Budget managed, e.g., '$50M'",
    )
    pl_responsibility: str | None = Field(
        default=None,
        description="P&L responsibility, e.g., '$100M'",
    )
    geography: str | None = Field(
        default=None,
        description="Geographic reach, e.g., 'Global', 'EMEA'",
    )
    customers: str | None = Field(
        default=None,
        description="Customer scope, e.g., 'Fortune 500', '500K users'",
    )
