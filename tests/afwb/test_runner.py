from __future__ import annotations

from src.afwb.runner import DeterministicRunner
from src.afwb.scenarios import load_scenarios
from src.afwb.schemas import TraceVariant
from src.afwb.trace import trace_to_json


def test_runner_generates_byte_stable_traces() -> None:
    runner = DeterministicRunner.create()
    scenarios = load_scenarios()

    first = [
        trace_to_json(runner.run(scenario, TraceVariant.MUTATED))
        for scenario in scenarios
    ]
    second = [
        trace_to_json(runner.run(scenario, TraceVariant.MUTATED))
        for scenario in scenarios
    ]

    assert first == second


def test_runner_computes_trace_totals_from_span_usage() -> None:
    runner = DeterministicRunner.create()
    scenario = load_scenarios()[0]

    trace = runner.run(scenario, TraceVariant.REFERENCE)

    assert trace.total_input_tokens == sum(
        span.usage.input_tokens for span in trace.spans
    )
    assert trace.total_output_tokens == sum(
        span.usage.output_tokens for span in trace.spans
    )
    assert trace.total_tool_calls == sum(span.usage.tool_calls for span in trace.spans)
    assert trace.total_latency_ms == sum(span.usage.latency_ms for span in trace.spans)
    assert trace.total_cost_usd == sum(span.usage.cost_usd for span in trace.spans)
