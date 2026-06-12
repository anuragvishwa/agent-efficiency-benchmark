from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.afwb.constants import AFWB_CONFIG_DIR


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_config(name: str) -> dict[str, Any]:
    path = AFWB_CONFIG_DIR / name
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"AFWB config {path} must contain a JSON object")
    return payload
