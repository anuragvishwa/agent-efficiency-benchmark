from __future__ import annotations

from dataclasses import dataclass, field

from src.afwb.runner import DeterministicRunner
from src.afwb.scenarios import load_gold_labels, load_scenarios
from src.afwb.schemas import ScenarioDefinition, TraceStatus, TraceVariant


@dataclass
class ValidationReport:
    scenario_count: int
    gold_count: int
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "scenario_count": self.scenario_count,
            "gold_count": self.gold_count,
            "errors": self.errors,
        }


def _check_unique(values: list[str], label: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            errors.append(f"Duplicate {label}: {value}")
        seen.add(value)


def validate_scenarios() -> ValidationReport:
    scenarios = load_scenarios()
    labels = load_gold_labels()
    errors: list[str] = []
    _check_unique([scenario.scenario_id for scenario in scenarios], "scenario_id", errors)
    _check_unique([label.scenario_id for label in labels], "gold scenario_id", errors)

    scenario_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    runner = DeterministicRunner.create()
    for scenario in scenarios:
        _validate_generated_traces(scenario, runner, errors)

    for label in labels:
        scenario = scenario_by_id.get(label.scenario_id)
        if scenario is None:
            errors.append(f"Gold label has no scenario: {label.scenario_id}")
            continue
        if label.root_cause_category != scenario.root_cause_category:
            errors.append(f"Gold category mismatch for {label.scenario_id}")
        if label.remediation != scenario.remediation:
            errors.append(f"Gold remediation mismatch for {label.scenario_id}")
        mutated_trace = runner.run(scenario, TraceVariant.MUTATED)
        mutated_span_ids = {span.span_id for span in mutated_trace.spans}
        if label.root_cause_span_id not in mutated_span_ids:
            errors.append(f"Gold root span missing for {label.scenario_id}")
        if label.first_observable_failure_span_id not in mutated_span_ids:
            errors.append(f"Gold first-observable span missing for {label.scenario_id}")

    return ValidationReport(
        scenario_count=len(scenarios),
        gold_count=len(labels),
        errors=errors,
    )


def _validate_generated_traces(
    scenario: ScenarioDefinition,
    runner: DeterministicRunner,
    errors: list[str],
) -> None:
    reference = runner.run(scenario, TraceVariant.REFERENCE)
    mutated = runner.run(scenario, TraceVariant.MUTATED)
    if reference.status != TraceStatus.PASSED:
        errors.append(f"Reference trace must pass: {scenario.scenario_id}")
    if mutated.status not in {TraceStatus.FAILED, TraceStatus.WASTEFUL}:
        errors.append(f"Mutated trace must fail or be wasteful: {scenario.scenario_id}")
