from __future__ import annotations

import math
from typing import Iterable


def safe_divide(numerator: float | int | None, denominator: float | int | None) -> float:
    if numerator is None or denominator in (None, 0):
        return 0.0
    return float(numerator) / float(denominator)


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    phat = successes / total
    denom = 1 + z**2 / total
    center = (phat + z**2 / (2 * total)) / denom
    margin = z * math.sqrt((phat * (1 - phat) + z**2 / (4 * total)) / total) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def cost_metrics_eligible(
    runs: int,
    positive_cost_coverage: float,
    min_runs: int = 20,
    min_positive_cost_coverage: float = 0.80,
) -> bool:
    return runs >= min_runs and positive_cost_coverage >= min_positive_cost_coverage


def macro_average(values: Iterable[float | None]) -> float:
    cleaned = [value for value in values if value is not None]
    if not cleaned:
        return 0.0
    return sum(cleaned) / len(cleaned)
