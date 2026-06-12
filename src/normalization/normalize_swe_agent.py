from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow.parquet as pq

from src.common.datasets import dataset_paths
from src.common.hashing import stable_sha256, text_sha256
from src.common.model_names import canonicalize_model_name
from src.common.text import clean_text, to_text
from src.normalization.normalize_terminalbench import RUN_SCHEMA, STEP_SCHEMA


SWE_AGENT_RUN_SCHEMA = {
    **RUN_SCHEMA,
    "exit_status": pl.String,
    "generated_patch_chars": pl.Int64,
    "generated_patch_hash": pl.String,
    "eval_log_chars": pl.Int64,
    "eval_log_hash": pl.String,
    "eval_error_summary": pl.String,
}

ACTION_BLOCK_PATTERN = re.compile(r"```(.*?)```", re.DOTALL)


def _source_revision() -> str | None:
    paths = dataset_paths("swe_agent")
    if not paths.source_metadata_path.exists():
        return None
    try:
        return json.loads(paths.source_metadata_path.read_text()).get("revision")
    except json.JSONDecodeError:
        return None


def _trajectory_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if hasattr(value, "tolist"):
        converted = value.tolist()
        return converted if isinstance(converted, list) else []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def build_run_id(row: dict[str, Any], seen_ids: dict[str, int]) -> tuple[str, str]:
    identity = {
        "instance_id": clean_text(row.get("instance_id")),
        "model_name": clean_text(row.get("model_name")),
        "target": row.get("target"),
        "exit_status": clean_text(row.get("exit_status")),
        "generated_patch": row.get("generated_patch"),
        "trajectory": row.get("trajectory"),
    }
    base_id = f"sweagent:derived:{stable_sha256(identity, length=24)}"
    duplicate_number = seen_ids.get(base_id, 0)
    seen_ids[base_id] = duplicate_number + 1
    if duplicate_number > 0:
        return f"{base_id}:duplicate-{duplicate_number + 1}", "derived_duplicate"
    return base_id, "derived"


def extract_action(text: str | None) -> str | None:
    text = clean_text(text)
    if text is None:
        return None
    blocks = []
    for match in ACTION_BLOCK_PATTERN.findall(text):
        block = match.strip()
        lines = block.splitlines()
        if len(lines) > 1 and lines[0].strip().lower() in {"bash", "sh", "python"}:
            block = "\n".join(lines[1:]).strip()
        blocks.append(block)
    if blocks:
        return blocks[-1] or None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for marker in ("submit", "open", "edit", "search", "bash"):
        for line in reversed(lines):
            if line.lower().startswith(marker):
                return line
    return lines[-1] if lines else text


def derive_tool_name(command: str | None, exit_status: str | None = None) -> str | None:
    value = (command or "").strip().lower()
    exit_value = (exit_status or "").strip().lower()
    if value.startswith("submit") or exit_value.startswith("submitted"):
        return "submit"
    if value.startswith("open") or "open file:" in value:
        return "open"
    if value.startswith("edit") or value.startswith("replace") or value.startswith("create"):
        return "edit"
    if value.startswith("search") or value.startswith("grep") or value.startswith("find"):
        return "search"
    if any(token in value for token in ("pytest", "python ", "bash", "ls ", "cat ", "sed ")):
        return "bash"
    return "swe_agent_action" if value else None


def _eval_error_summary(eval_logs: str | None) -> str | None:
    if not eval_logs:
        return None
    patterns = [
        "traceback",
        "failed",
        "error",
        "assertionerror",
        "syntaxerror",
        "modulenotfounderror",
        "permission denied",
        "timeout",
    ]
    lower = eval_logs.lower()
    found = [pattern for pattern in patterns if pattern in lower]
    return ",".join(found) if found else None


def normalize_trajectory(
    *,
    run_id: str,
    task_name: str,
    trajectory: list[Any],
    exit_status: str | None,
) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    tool_call_count = 0
    pending_ai: dict[str, Any] | None = None
    step_index = 0

    for turn in trajectory:
        if not isinstance(turn, dict):
            rows.append(
                {
                    "run_id": run_id,
                    "task_name": task_name,
                    "step_index": step_index,
                    "tool_index": None,
                    "source": None,
                    "message": to_text(turn),
                    "tool_name": None,
                    "command": None,
                    "observation": None,
                }
            )
            step_index += 1
            continue

        role = clean_text(turn.get("role"))
        text = to_text(turn.get("text"))
        system_prompt = to_text(turn.get("system_prompt"))
        if role == "system":
            rows.append(
                {
                    "run_id": run_id,
                    "task_name": task_name,
                    "step_index": step_index,
                    "tool_index": None,
                    "source": "system",
                    "message": system_prompt,
                    "tool_name": None,
                    "command": None,
                    "observation": None,
                }
            )
            step_index += 1
            continue

        if role == "ai":
            if pending_ai is not None:
                rows.append(pending_ai)
                step_index += 1
            command = extract_action(text)
            pending_ai = {
                "run_id": run_id,
                "task_name": task_name,
                "step_index": step_index,
                "tool_index": 0 if command else None,
                "source": "ai",
                "message": text,
                "tool_name": derive_tool_name(command, exit_status),
                "command": command,
                "observation": None,
            }
            if command:
                tool_call_count += 1
            continue

        if role == "user" and pending_ai is not None:
            pending_ai["observation"] = text
            rows.append(pending_ai)
            pending_ai = None
            step_index += 1
            continue

        rows.append(
            {
                "run_id": run_id,
                "task_name": task_name,
                "step_index": step_index,
                "tool_index": None,
                "source": role,
                "message": text,
                "tool_name": None,
                "command": None,
                "observation": None,
            }
        )
        step_index += 1

    if pending_ai is not None:
        rows.append(pending_ai)

    return rows, tool_call_count


def _write_batch(
    rows: list[dict[str, Any]],
    schema: dict[str, pl.DataType],
    writer: pq.ParquetWriter | None,
    path: Path,
) -> pq.ParquetWriter | None:
    if not rows:
        return writer
    df = pl.DataFrame(rows, schema=schema, strict=False)
    table = df.to_arrow()
    if writer is None:
        writer = pq.ParquetWriter(path, table.schema, compression="zstd")
    writer.write_table(table)
    rows.clear()
    return writer


def main() -> None:
    paths = dataset_paths("swe_agent")
    if not paths.raw_path.exists():
        raise FileNotFoundError(
            f"SWE-agent raw dataset not found at {paths.raw_path}. "
            "Run python -m src.ingestion.download_swe_agent first."
        )

    source_revision = _source_revision()
    run_rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []
    seen_ids: dict[str, int] = {}
    normalized_step_count = 0
    run_writer: pq.ParquetWriter | None = None
    step_writer: pq.ParquetWriter | None = None
    run_tmp_path = paths.runs_path.with_suffix(paths.runs_path.suffix + ".tmp")
    step_tmp_path = paths.steps_path.with_suffix(paths.steps_path.suffix + ".tmp")
    paths.runs_path.parent.mkdir(parents=True, exist_ok=True)
    for tmp_path in (run_tmp_path, step_tmp_path):
        if tmp_path.exists():
            tmp_path.unlink()

    parquet_file = pq.ParquetFile(paths.raw_path)
    total_runs = parquet_file.metadata.num_rows
    processed = 0
    for batch in parquet_file.iter_batches(batch_size=1_000):
        for row in batch.to_pylist():
            processed += 1
            run_id, run_id_source = build_run_id(row, seen_ids)
            instance_id = to_text(row.get("instance_id"))
            model_raw = to_text(row.get("model_name"))
            success = bool(row.get("target")) if row.get("target") is not None else None
            reward = 1 if success else 0 if success is not None else None
            exit_status = to_text(row.get("exit_status"))
            generated_patch = to_text(row.get("generated_patch")) or ""
            eval_logs = to_text(row.get("eval_logs")) or ""
            trajectory = _trajectory_list(row.get("trajectory"))

            normalized_steps, tool_call_count = normalize_trajectory(
                run_id=run_id,
                task_name=instance_id or "",
                trajectory=trajectory,
                exit_status=exit_status,
            )
            normalized_step_count += len(normalized_steps)
            step_rows.extend(normalized_steps)
            run_rows.append(
                {
                    "run_id": run_id,
                    "run_id_source": run_id_source,
                    "source_dataset": "swe_agent",
                    "source_revision": source_revision,
                    "source_row_number": processed,
                    "task_name": instance_id,
                    "agent": "swe-agent",
                    "model_raw": model_raw,
                    "model": canonicalize_model_name(model_raw),
                    "success": success,
                    "reward": reward,
                    "duration_seconds": None,
                    "input_tokens": None,
                    "output_tokens": None,
                    "cache_tokens": None,
                    "cost_usd": None,
                    "cost_status": "missing",
                    "trial_name": instance_id,
                    "started_at_raw": None,
                    "ended_at_raw": None,
                    "started_at": None,
                    "ended_at": None,
                    "step_count": len(trajectory),
                    "tool_call_count": tool_call_count,
                    "has_steps": len(trajectory) > 0,
                    "has_cost": False,
                    "has_positive_cost": False,
                    "has_duration": False,
                    "has_tokens": False,
                    "exit_status": exit_status,
                    "generated_patch_chars": len(generated_patch),
                    "generated_patch_hash": text_sha256(generated_patch, length=24)
                    if generated_patch
                    else None,
                    "eval_log_chars": len(eval_logs),
                    "eval_log_hash": text_sha256(eval_logs, length=24)
                    if eval_logs
                    else None,
                    "eval_error_summary": _eval_error_summary(eval_logs),
                }
            )
        if processed % 5_000 == 0 or processed == total_runs:
            run_writer = _write_batch(
                run_rows,
                SWE_AGENT_RUN_SCHEMA,
                run_writer,
                run_tmp_path,
            )
            step_writer = _write_batch(
                step_rows,
                STEP_SCHEMA,
                step_writer,
                step_tmp_path,
            )
            print(
                f"Processed {processed:,}/{total_runs:,} SWE-agent runs "
                f"({normalized_step_count:,} step events)"
            )

    run_writer = _write_batch(run_rows, SWE_AGENT_RUN_SCHEMA, run_writer, run_tmp_path)
    step_writer = _write_batch(step_rows, STEP_SCHEMA, step_writer, step_tmp_path)
    if run_writer is None or step_writer is None:
        raise RuntimeError("No SWE-agent rows were written")
    run_writer.close()
    step_writer.close()
    run_tmp_path.replace(paths.runs_path)
    step_tmp_path.replace(paths.steps_path)

    run_count = pl.scan_parquet(paths.runs_path).select(pl.len()).collect().item()
    step_count = pl.scan_parquet(paths.steps_path).select(pl.len()).collect().item()
    print("\nSWE-agent normalization complete")
    print(f"Runs:        {run_count:,}")
    print(f"Step events: {step_count:,}")
    print(f"Runs saved:  {paths.runs_path}")
    print(f"Steps saved: {paths.steps_path}")


if __name__ == "__main__":
    main()
