from __future__ import annotations

from pathlib import Path

from pydantic import TypeAdapter

from src.afwb.config import load_json
from src.afwb.constants import FOUNDATION_GOLD_FILE, FOUNDATION_SCENARIO_FILE
from src.afwb.schemas import GoldLabel, ScenarioDefinition


_SCENARIOS = TypeAdapter(list[ScenarioDefinition])
_GOLD = TypeAdapter(list[GoldLabel])


def load_scenarios(path: Path = FOUNDATION_SCENARIO_FILE) -> list[ScenarioDefinition]:
    scenarios = _SCENARIOS.validate_python(load_json(path))
    return sorted(scenarios, key=lambda scenario: scenario.scenario_id)


def load_gold_labels(path: Path = FOUNDATION_GOLD_FILE) -> list[GoldLabel]:
    labels = _GOLD.validate_python(load_json(path))
    return sorted(labels, key=lambda label: label.scenario_id)


def scenario_by_id(
    scenarios: list[ScenarioDefinition] | None = None,
) -> dict[str, ScenarioDefinition]:
    selected = scenarios if scenarios is not None else load_scenarios()
    return {scenario.scenario_id: scenario for scenario in selected}


def gold_by_id(labels: list[GoldLabel] | None = None) -> dict[str, GoldLabel]:
    selected = labels if labels is not None else load_gold_labels()
    return {label.scenario_id: label for label in selected}
