from __future__ import annotations

from src.benchmarks.metrics import cost_metrics_eligible, safe_divide, wilson_interval


def test_wilson_interval_bounds() -> None:
    low, high = wilson_interval(5, 10)
    assert 0 <= low <= high <= 1


def test_cost_eligibility_requires_coverage_and_runs() -> None:
    assert cost_metrics_eligible(20, 0.8)
    assert not cost_metrics_eligible(19, 1.0)
    assert not cost_metrics_eligible(20, 0.79)


def test_safe_divide_zero_denominator() -> None:
    assert safe_divide(1, 0) == 0
    assert safe_divide(4, 2) == 2
