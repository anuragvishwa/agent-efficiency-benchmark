from __future__ import annotations

import json
from pathlib import Path

from src.afwb.schemas import Trace


def trace_to_json(trace: Trace) -> str:
    return json.dumps(trace.model_dump(mode="json"), separators=(",", ":"), sort_keys=True)


def write_jsonl(path: Path, traces: list[Trace]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{trace_to_json(trace)}\n" for trace in traces))


def read_jsonl(path: Path) -> list[Trace]:
    return [
        Trace.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]
