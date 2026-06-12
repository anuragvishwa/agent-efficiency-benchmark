from __future__ import annotations

from src.reports.schemas import PublicBenchmark


def test_public_benchmark_schema_accepts_required_shape() -> None:
    payload = {
        "metadata": {},
        "coverage": {},
        "overview": {},
        "systems": [],
        "agents": [],
        "models_uncontrolled": [],
        "tasks": [],
        "failure_patterns": [],
        "early_stopping": [],
        "examples": [],
        "datasets": [],
    }
    assert PublicBenchmark.model_validate(payload)
