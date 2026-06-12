from __future__ import annotations

import json
import re
from typing import Any


def to_text(value: Any) -> str | None:
    """Convert heterogeneous public-dataset values into safe deterministic text."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def clean_text(value: Any) -> str | None:
    text = to_text(value)
    if text is None:
        return None
    text = text.strip()
    return text or None


def collapse_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.replace("\r\n", "\n").replace("\r", "\n")).strip()
