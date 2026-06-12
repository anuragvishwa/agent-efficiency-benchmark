from __future__ import annotations

from src.afwb.runner import DeterministicRunner
from src.afwb.scenarios import gold_by_id, load_gold_labels, load_scenarios
from src.afwb.schemas import RootCauseCategory, TraceVariant
from src.afwb.validation import validate_scenarios


EXPECTED_ROOT_CAUSES = {
    "invalid_booking_date": RootCauseCategory.TOOL_ARGUMENT_ERROR,
    "duplicate_payment": RootCauseCategory.SIDE_EFFECT_DUPLICATION,
    "infinite_retry_terminal_error": RootCauseCategory.TOOL_RETRY_STORM,
    "missing_loop_exit_condition": RootCauseCategory.LOOP_NON_TERMINATION,
}

EXPECTED_REMEDIATIONS = {
    "invalid_booking_date": "validate_iso_date_before_booking_v1",
    "duplicate_payment": "use_idempotency_key_payment_v1",
    "infinite_retry_terminal_error": "mark_4xx_non_retryable_v1",
    "missing_loop_exit_condition": "stop_on_success_flag_v1",
}


def test_foundation_scenarios_have_expected_gold_labels() -> None:
    labels = gold_by_id(load_gold_labels())

    assert set(labels) == set(EXPECTED_ROOT_CAUSES)
    for scenario_id, category in EXPECTED_ROOT_CAUSES.items():
        label = labels[scenario_id]
        assert label.failed
        assert label.root_cause_category == category
        assert label.remediation.remediation_id == EXPECTED_REMEDIATIONS[scenario_id]


def test_gold_spans_exist_in_mutated_traces() -> None:
    runner = DeterministicRunner.create()
    labels = gold_by_id(load_gold_labels())

    for scenario in load_scenarios():
        trace = runner.run(scenario, TraceVariant.MUTATED)
        span_ids = {span.span_id for span in trace.spans}
        label = labels[scenario.scenario_id]
        assert label.root_cause_span_id in span_ids
        assert label.first_observable_failure_span_id in span_ids


def test_foundation_validation_report_passes() -> None:
    report = validate_scenarios()

    assert report.ok
    assert report.scenario_count == 4
    assert report.gold_count == 4
