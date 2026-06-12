from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PublicBenchmark(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)
    coverage: dict[str, Any] = Field(default_factory=dict)
    overview: dict[str, Any] = Field(default_factory=dict)
    systems: list[dict[str, Any]] = Field(default_factory=list)
    agents: list[dict[str, Any]] = Field(default_factory=list)
    models_uncontrolled: list[dict[str, Any]] = Field(default_factory=list)
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    failure_patterns: list[dict[str, Any]] = Field(default_factory=list)
    early_stopping: list[dict[str, Any]] = Field(default_factory=list)
    examples: list[dict[str, Any]] = Field(default_factory=list)
    datasets: list[dict[str, Any]] = Field(default_factory=list)
