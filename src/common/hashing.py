from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_sha256(value: Any, length: int | None = None) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


def text_sha256(value: str, length: int | None = None) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length] if length else digest
