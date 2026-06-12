from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.afwb.schemas import ResourceUsage, SpanStatus


@dataclass(frozen=True)
class MockToolResult:
    output: dict[str, Any]
    status: SpanStatus
    usage: ResourceUsage


class MockToolRegistry:
    """Deterministic mock tools used by AFWB Lite foundation scenarios."""

    KNOWN_TOOLS = {
        "booking_adapter.create_booking",
        "date_normalizer.validate_iso_date",
        "http_client.fetch_resource",
        "payment_adapter.charge",
        "planner_executor.check_loop_exit",
        "planner_executor.execute_task",
        "retry_policy.classify_error",
    }

    def execute(
        self,
        *,
        name: str,
        payload: dict[str, Any],
        expected_output: dict[str, Any],
        status: SpanStatus,
        usage: ResourceUsage,
    ) -> MockToolResult:
        _ = payload
        if name not in self.KNOWN_TOOLS:
            raise ValueError(f"Unknown AFWB mock tool: {name}")
        return MockToolResult(output=expected_output, status=status, usage=usage)
