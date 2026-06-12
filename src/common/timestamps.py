from __future__ import annotations

from datetime import datetime, timezone

from src.common.text import clean_text


def parse_timestamp(value: object) -> datetime | None:
    text = clean_text(value)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
