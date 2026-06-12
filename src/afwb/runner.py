from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.afwb.constants import BASE_TIMESTAMP, FRAMEWORK, MOCK_MODEL_NAME
from src.afwb.mock_model import MockModel
from src.afwb.mock_tools import MockToolRegistry
from src.afwb.schemas import (
    ResourceUsage,
    ScenarioDefinition,
    ScenarioStepSpec,
    Span,
    Trace,
    TraceVariant,
)


def _parse_base_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


@dataclass
class DeterministicRunner:
    mock_model: MockModel
    mock_tools: MockToolRegistry

    @classmethod
    def create(cls) -> DeterministicRunner:
        return cls(mock_model=MockModel(), mock_tools=MockToolRegistry())

    def run(self, scenario: ScenarioDefinition, variant: TraceVariant) -> Trace:
        run_spec = scenario.reference if variant == TraceVariant.REFERENCE else scenario.mutated
        spans: list[Span] = []
        total_usage = ResourceUsage()
        cursor = _parse_base_timestamp(BASE_TIMESTAMP)
        for step in run_spec.steps:
            started_at = cursor
            cursor = cursor + timedelta(milliseconds=step.usage.latency_ms)
            spans.append(self._span_from_step(step, started_at, cursor))
            total_usage += step.usage

        return Trace(
            run_id=f"{variant.value}_{scenario.scenario_id}_seed_{scenario.seed}",
            scenario_id=scenario.scenario_id,
            variant=variant,
            framework=FRAMEWORK,
            model=MOCK_MODEL_NAME,
            seed=scenario.seed,
            status=run_spec.expected_status,
            started_at=_format_timestamp(_parse_base_timestamp(BASE_TIMESTAMP)),
            ended_at=_format_timestamp(cursor),
            total_input_tokens=total_usage.input_tokens,
            total_output_tokens=total_usage.output_tokens,
            total_tool_calls=total_usage.tool_calls,
            total_cost_usd=total_usage.cost_usd,
            total_latency_ms=total_usage.latency_ms,
            spans=spans,
        )

    def _span_from_step(
        self,
        step: ScenarioStepSpec,
        started_at: datetime,
        ended_at: datetime,
    ) -> Span:
        if step.type == "model":
            result = self.mock_model.invoke(
                name=step.name,
                prompt=step.input,
                expected_output=step.output,
                status=step.status,
                usage=step.usage,
            )
        elif step.type == "tool":
            result = self.mock_tools.execute(
                name=step.name,
                payload=step.input,
                expected_output=step.output,
                status=step.status,
                usage=step.usage,
            )
        else:
            result = self.mock_model.invoke(
                name=step.name,
                prompt=step.input,
                expected_output=step.output,
                status=step.status,
                usage=step.usage,
            )
        return Span(
            span_id=step.span_id,
            parent_span_id=step.parent_span_id,
            type=step.type,
            name=step.name,
            status=result.status,
            input=step.input,
            output=result.output,
            started_at=_format_timestamp(started_at),
            ended_at=_format_timestamp(ended_at),
            latency_ms=result.usage.latency_ms,
            usage=result.usage,
            metadata=step.metadata,
        )
