from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.afwb.schemas import ResourceUsage, SpanStatus


@dataclass(frozen=True)
class MockModelResult:
    output: dict[str, Any]
    status: SpanStatus
    usage: ResourceUsage


class MockModel:
    """A deterministic scripted model with no API or environment access."""

    def invoke(
        self,
        *,
        name: str,
        prompt: dict[str, Any],
        expected_output: dict[str, Any],
        status: SpanStatus,
        usage: ResourceUsage,
    ) -> MockModelResult:
        _ = (name, prompt)
        return MockModelResult(output=expected_output, status=status, usage=usage)
