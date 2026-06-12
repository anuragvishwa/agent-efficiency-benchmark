from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl

from src.common.constants import (
    RAW_TERMINALBENCH_PATH,
    RUNS_PATH,
    SOURCE_DATASET,
    SOURCE_METADATA_PATH,
    STEPS_PATH,
)
from src.common.hashing import stable_sha256
from src.common.model_names import canonicalize_model_name
from src.common.numeric import to_float, to_int
from src.common.text import clean_text, to_text
from src.common.timestamps import parse_timestamp


RUN_SCHEMA = {
    "run_id": pl.String,
    "run_id_source": pl.String,
    "source_dataset": pl.String,
    "source_revision": pl.String,
    "source_row_number": pl.Int64,
    "task_name": pl.String,
    "agent": pl.String,
    "model_raw": pl.String,
    "model": pl.String,
    "success": pl.Boolean,
    "reward": pl.Int64,
    "duration_seconds": pl.Float64,
    "input_tokens": pl.Float64,
    "output_tokens": pl.Float64,
    "cache_tokens": pl.Float64,
    "cost_usd": pl.Float64,
    "cost_status": pl.String,
    "trial_name": pl.String,
    "started_at_raw": pl.String,
    "ended_at_raw": pl.String,
    "started_at": pl.Datetime("us", "UTC"),
    "ended_at": pl.Datetime("us", "UTC"),
    "step_count": pl.Int64,
    "tool_call_count": pl.Int64,
    "has_steps": pl.Boolean,
    "has_cost": pl.Boolean,
    "has_positive_cost": pl.Boolean,
    "has_duration": pl.Boolean,
    "has_tokens": pl.Boolean,
}


STEP_SCHEMA = {
    "run_id": pl.String,
    "task_name": pl.String,
    "step_index": pl.Int64,
    "tool_index": pl.Int64,
    "source": pl.String,
    "message": pl.String,
    "tool_name": pl.String,
    "command": pl.String,
    "observation": pl.String,
}


def parse_steps(value: Any) -> list[Any]:
    """Parse Terminal-Bench trajectory JSON defensively."""
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return []
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def build_run_id(row: dict[str, Any], seen_ids: dict[str, int]) -> tuple[str, str]:
    trial_id = clean_text(row.get("trial_id"))
    if trial_id is not None:
        base_id = f"terminalbench:trial:{trial_id}"
        id_source = "trial_id"
    else:
        identity = {
            "trial_name": clean_text(row.get("trial_name")),
            "task_name": clean_text(row.get("task_name")),
            "agent": clean_text(row.get("agent")),
            "model_raw": clean_text(row.get("model")),
            "started_at_raw": clean_text(row.get("started_at")),
            "ended_at_raw": clean_text(row.get("ended_at")),
            "reward": to_int(row.get("reward")),
            "steps": row.get("steps"),
        }
        base_id = f"terminalbench:derived:{stable_sha256(identity, length=24)}"
        id_source = "derived"

    duplicate_number = seen_ids.get(base_id, 0)
    seen_ids[base_id] = duplicate_number + 1
    if duplicate_number > 0:
        duplicate_source = (
            "trial_id_duplicate" if id_source == "trial_id" else "derived_duplicate"
        )
        return f"{base_id}:duplicate-{duplicate_number + 1}", duplicate_source
    return base_id, id_source


def normalize_tools(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return [value]


def get_tool_name(tool: dict[str, Any]) -> Any:
    for key in ("fn", "name", "tool", "function"):
        if key in tool and tool[key] is not None:
            return tool[key]
    return None


def get_tool_command(tool: dict[str, Any]) -> Any:
    for key in ("cmd", "arguments", "input", "params"):
        if key in tool and tool[key] is not None:
            return tool[key]
    return None


def normalize_step(
    *,
    run_id: str,
    task_name: str | None,
    step_index: int,
    step: Any,
) -> tuple[list[dict[str, Any]], int]:
    normalized_rows: list[dict[str, Any]] = []
    if not isinstance(step, dict):
        normalized_rows.append(
            {
                "run_id": run_id,
                "task_name": task_name,
                "step_index": step_index,
                "tool_index": None,
                "source": None,
                "message": to_text(step),
                "tool_name": None,
                "command": None,
                "observation": None,
            }
        )
        return normalized_rows, 0

    source = to_text(step.get("src"))
    message = to_text(step.get("msg"))
    observation = to_text(step.get("obs"))
    tools = normalize_tools(step.get("tools"))

    if not tools:
        normalized_rows.append(
            {
                "run_id": run_id,
                "task_name": task_name,
                "step_index": step_index,
                "tool_index": None,
                "source": source,
                "message": message,
                "tool_name": None,
                "command": None,
                "observation": observation,
            }
        )
        return normalized_rows, 0

    tool_call_count = 0
    for tool_index, tool in enumerate(tools):
        tool_call_count += 1
        if isinstance(tool, dict):
            tool_name = to_text(get_tool_name(tool))
            command = to_text(get_tool_command(tool))
        else:
            tool_name = None
            command = to_text(tool)
        normalized_rows.append(
            {
                "run_id": run_id,
                "task_name": task_name,
                "step_index": step_index,
                "tool_index": tool_index,
                "source": source,
                "message": message,
                "tool_name": tool_name,
                "command": command,
                "observation": observation,
            }
        )
    return normalized_rows, tool_call_count


def _source_revision() -> str | None:
    if not SOURCE_METADATA_PATH.exists():
        return None
    try:
        return json.loads(SOURCE_METADATA_PATH.read_text()).get("revision")
    except json.JSONDecodeError:
        return None


def _atomic_write_parquet(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    df.write_parquet(tmp_path, compression="zstd")
    tmp_path.replace(path)


def main() -> None:
    if not RAW_TERMINALBENCH_PATH.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {RAW_TERMINALBENCH_PATH}. "
            "Run the Terminal-Bench downloader first."
        )

    source = pl.read_parquet(RAW_TERMINALBENCH_PATH)
    source_revision = _source_revision()
    run_rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []
    seen_ids: dict[str, int] = {}

    malformed_steps = 0
    malformed_trajectories = 0
    total_runs = source.height

    for row_number, row in enumerate(source.iter_rows(named=True), start=1):
        run_id, run_id_source = build_run_id(row, seen_ids)
        task_name = to_text(row.get("task_name"))
        steps = parse_steps(row.get("steps"))

        if row.get("steps") and not steps:
            malformed_trajectories += 1

        tool_call_count = 0
        for step_index, step in enumerate(steps):
            if not isinstance(step, dict):
                malformed_steps += 1
            normalized_rows, calls_found = normalize_step(
                run_id=run_id,
                task_name=task_name,
                step_index=step_index,
                step=step,
            )
            step_rows.extend(normalized_rows)
            tool_call_count += calls_found

        reward = to_int(row.get("reward"))
        duration_seconds = to_float(row.get("duration_seconds"))
        input_tokens = to_float(row.get("input_tokens"))
        output_tokens = to_float(row.get("output_tokens"))
        cache_tokens = to_float(row.get("cache_tokens"))
        cost_cents = to_float(row.get("cost_cents"))
        cost_usd = cost_cents / 100.0 if cost_cents is not None else None
        if cost_usd is None:
            cost_status = "missing"
        elif cost_usd > 0:
            cost_status = "positive"
        else:
            cost_status = "zero"

        model_raw = to_text(row.get("model"))
        started_at_raw = to_text(row.get("started_at"))
        ended_at_raw = to_text(row.get("ended_at"))

        run_rows.append(
            {
                "run_id": run_id,
                "run_id_source": run_id_source,
                "source_dataset": SOURCE_DATASET,
                "source_revision": source_revision,
                "source_row_number": row_number,
                "task_name": task_name,
                "agent": to_text(row.get("agent")),
                "model_raw": model_raw,
                "model": canonicalize_model_name(model_raw),
                "success": reward == 1 if reward is not None else None,
                "reward": reward,
                "duration_seconds": duration_seconds,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_tokens": cache_tokens,
                "cost_usd": cost_usd,
                "cost_status": cost_status,
                "trial_name": to_text(row.get("trial_name")),
                "started_at_raw": started_at_raw,
                "ended_at_raw": ended_at_raw,
                "started_at": parse_timestamp(started_at_raw),
                "ended_at": parse_timestamp(ended_at_raw),
                "step_count": len(steps),
                "tool_call_count": tool_call_count,
                "has_steps": len(steps) > 0,
                "has_cost": cost_usd is not None,
                "has_positive_cost": cost_usd is not None and cost_usd > 0,
                "has_duration": duration_seconds is not None,
                "has_tokens": any(
                    value is not None
                    for value in (input_tokens, output_tokens, cache_tokens)
                ),
            }
        )

        if row_number % 5_000 == 0 or row_number == total_runs:
            print(
                f"Processed {row_number:,}/{total_runs:,} runs "
                f"({len(step_rows):,} step events)"
            )

    runs_df = pl.DataFrame(run_rows, schema=RUN_SCHEMA, strict=False)
    steps_df = pl.DataFrame(step_rows, schema=STEP_SCHEMA, strict=False)

    _atomic_write_parquet(runs_df, RUNS_PATH)
    _atomic_write_parquet(steps_df, STEPS_PATH)

    print("\nNormalization complete")
    print(f"Runs:                   {runs_df.height:,}")
    print(f"Step events:            {steps_df.height:,}")
    print(f"Malformed step values:  {malformed_steps:,}")
    print(f"Empty/malformed traces: {malformed_trajectories:,}")
    print(f"Runs saved to:          {RUNS_PATH}")
    print(f"Steps saved to:         {STEPS_PATH}")


if __name__ == "__main__":
    main()
