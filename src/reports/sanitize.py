from __future__ import annotations

import re


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[A-Za-z0-9+/=\[\]\{\}_-]*"),
    re.compile(r"(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"hf_[A-Za-z0-9_]{20,}"),
]


def sanitize_text(value: str | None) -> str | None:
    if value is None:
        return None
    output = value
    for pattern in SECRET_PATTERNS:
        output = pattern.sub("[REDACTED_SECRET]", output)
    return output
