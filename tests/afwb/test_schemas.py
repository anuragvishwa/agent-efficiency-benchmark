from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.afwb.schemas import (
    RemediationSpec,
    ResourceUsage,
    RootCauseCategory,
    ScenarioDefinition,
    Span,
    SpanStatus,
    Trace,
    TraceStatus,
    TraceVariant,
)


def test_resource_usage_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        ResourceUsage(input_tokens=-1)


def test_trace_rejects_total_mismatch() -> None:
    span = Span(
        span_id="span_001",
        type="model",
        name="mock.step",
        status=SpanStatus.OK,
        started_at="2026-06-12T10:00:00.000Z",
        ended_at="2026-06-12T10:00:00.010Z",
        latency_ms=10,
        usage=ResourceUsage(input_tokens=1, latency_ms=10),
    )

    with pytest.raises(ValidationError):
        Trace(
            run_id="reference_test_seed_42",
            scenario_id="test",
            variant=TraceVariant.REFERENCE,
            framework="custom",
            model="mock",
            seed=42,
            status=TraceStatus.PASSED,
            started_at="2026-06-12T10:00:00.000Z",
            ended_at="2026-06-12T10:00:00.010Z",
            total_input_tokens=2,
            total_output_tokens=0,
            total_tool_calls=0,
            total_cost_usd=0,
            total_latency_ms=10,
            spans=[span],
        )


def test_scenario_rejects_unknown_taxonomy_value() -> None:
    payload = {
        "scenario_id": "bad_category",
        "name": "Bad category",
        "family": "Tool use and control flow",
        "description": "Invalid taxonomy should fail validation.",
        "root_cause_category": "NOT_A_CATEGORY",
        "mutation": "bad taxonomy",
        "symptom": "validation failure",
        "remediation": {
            "remediation_type": "TERMINATION_CONDITION",
            "remediation_id": "stop_on_success_flag_v1",
            "target_component": "planner_executor_loop",
        },
        "reference": {
            "expected_status": "passed",
            "steps": [
                {
                    "span_id": "span_001",
                    "type": "model",
                    "name": "mock.step",
                    "status": "ok",
                }
            ],
        },
        "mutated": {
            "expected_status": "failed",
            "steps": [
                {
                    "span_id": "span_001",
                    "type": "model",
                    "name": "mock.step",
                    "status": "error",
                }
            ],
        },
    }

    with pytest.raises(ValidationError):
        ScenarioDefinition.model_validate(payload)


def test_scenario_rejects_missing_parent_span() -> None:
    payload = {
        "scenario_id": "bad_parent",
        "name": "Bad parent",
        "family": "Tool use and control flow",
        "description": "Invalid parent should fail validation.",
        "root_cause_category": RootCauseCategory.LOOP_NON_TERMINATION,
        "mutation": "bad parent",
        "symptom": "validation failure",
        "remediation": RemediationSpec(
            remediation_type="TERMINATION_CONDITION",
            remediation_id="stop_on_success_flag_v1",
            target_component="planner_executor_loop",
        ),
        "reference": {
            "expected_status": "passed",
            "steps": [
                {
                    "span_id": "span_001",
                    "parent_span_id": "span_missing",
                    "type": "model",
                    "name": "mock.step",
                    "status": "ok",
                }
            ],
        },
        "mutated": {
            "expected_status": "failed",
            "steps": [
                {
                    "span_id": "span_001",
                    "type": "model",
                    "name": "mock.step",
                    "status": "error",
                }
            ],
        },
    }

    with pytest.raises(ValidationError):
        ScenarioDefinition.model_validate(payload)
