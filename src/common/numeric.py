from __future__ import annotations

import math
from typing import Any


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def to_int(value: Any) -> int | None:
    number = to_float(value)
    if number is None:
        return None
    try:
        return int(number)
    except (OverflowError, ValueError):
        return None
