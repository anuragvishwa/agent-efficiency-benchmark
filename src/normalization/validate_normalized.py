from __future__ import annotations

import json
import argparse
from datetime import datetime, timezone
from typing import Any

import polars as pl

from src.common.constants import (
    DOCS_DIR,
    METHODOLOGY_VERSION,
)
from src.common.datasets import DatasetPaths, dataset_paths


RUN_REQUIRED_COLUMNS = {
    "run_id",
    "run_id_source",
    "source_dataset",
    "source_revision",
    "source_row_number",
    "task_name",
    "agent",
    "model_raw",
    "model",
    "success",
    "reward",
    "duration_seconds",
    "input_tokens",
    "output_tokens",
    "cache_tokens",
    "cost_usd",
    "cost_status",
    "trial_name",
    "started_at_raw",
    "ended_at_raw",
    "started_at",
    "ended_at",
    "step_count",
    "tool_call_count",
    "has_steps",
    "has_cost",
    "has_positive_cost",
    "has_duration",
    "has_tokens",
}

STEP_REQUIRED_COLUMNS = {
    "run_id",
    "task_name",
    "step_index",
    "tool_index",
    "source",
    "message",
    "tool_name",
    "command",
    "observation",
}

ALLOWED_RUN_ID_SOURCES = {
    "trial_id",
    "derived",
    "trial_id_duplicate",
    "derived_duplicate",
}


def _source_metadata(paths: DatasetPaths) -> dict[str, Any]:
    if not paths.source_metadata_path.exists():
        return {}
    try:
        return json.loads(paths.source_metadata_path.read_text())
    except json.JSONDecodeError:
        return {}


def _finite_violation_count(df: pl.DataFrame, column: str) -> int:
    return df.filter(pl.col(column).is_not_null() & ~pl.col(column).is_finite()).height


def _failures(runs: pl.DataFrame, steps: pl.DataFrame) -> list[str]:
    failures: list[str] = []
    missing_run_cols = RUN_REQUIRED_COLUMNS - set(runs.columns)
    missing_step_cols = STEP_REQUIRED_COLUMNS - set(steps.columns)
    if missing_run_cols:
        failures.append(f"Missing run columns: {sorted(missing_run_cols)}")
    if missing_step_cols:
        failures.append(f"Missing step columns: {sorted(missing_step_cols)}")
    if failures:
        return failures

    duplicate_runs = runs.select(pl.col("run_id").is_duplicated().sum()).item()
    if duplicate_runs:
        failures.append(f"run_id is not unique: {duplicate_runs:,} duplicate rows")

    missing_step_runs = steps.join(runs.select("run_id"), on="run_id", how="anti").height
    if missing_step_runs:
        failures.append(f"{missing_step_runs:,} steps reference missing runs")

    for column in ("cost_usd", "duration_seconds"):
        invalid = _finite_violation_count(runs, column)
        if invalid:
            failures.append(f"{column} has {invalid:,} non-finite values")

    bad_has_steps = runs.filter(pl.col("has_steps") != (pl.col("step_count") > 0)).height
    if bad_has_steps:
        failures.append(f"has_steps mismatch rows: {bad_has_steps:,}")

    bad_positive_cost = runs.filter(
        pl.col("has_positive_cost")
        != (pl.col("cost_usd").is_not_null() & (pl.col("cost_usd") > 0))
    ).height
    if bad_positive_cost:
        failures.append(f"has_positive_cost mismatch rows: {bad_positive_cost:,}")

    bad_cost_status = runs.filter(
        (
            (pl.col("cost_usd").is_null() & (pl.col("cost_status") != "missing"))
            | ((pl.col("cost_usd") == 0) & (pl.col("cost_status") != "zero"))
            | ((pl.col("cost_usd") > 0) & (pl.col("cost_status") != "positive"))
        )
    ).height
    if bad_cost_status:
        failures.append(f"cost_status mismatch rows: {bad_cost_status:,}")

    bad_success = runs.filter(
        pl.col("reward").is_not_null() & (pl.col("success") != (pl.col("reward") == 1))
    ).height
    if bad_success:
        failures.append(f"success/reward mismatch rows: {bad_success:,}")

    for column in ("source_row_number", "step_count", "tool_call_count"):
        bad = runs.filter(pl.col(column).is_not_null() & (pl.col(column) < 0)).height
        if bad:
            failures.append(f"{column} has negative values: {bad:,}")

    bad_step_indexes = steps.filter(pl.col("step_index").is_not_null() & (pl.col("step_index") < 0)).height
    bad_tool_indexes = steps.filter(pl.col("tool_index").is_not_null() & (pl.col("tool_index") < 0)).height
    if bad_step_indexes:
        failures.append(f"step_index has negative values: {bad_step_indexes:,}")
    if bad_tool_indexes:
        failures.append(f"tool_index has negative values: {bad_tool_indexes:,}")

    bad_sources = runs.filter(~pl.col("run_id_source").is_in(ALLOWED_RUN_ID_SOURCES)).height
    if bad_sources:
        failures.append(f"Invalid run_id_source rows: {bad_sources:,}")

    return failures


def _quality_profile(
    runs: pl.DataFrame,
    steps: pl.DataFrame,
    paths: DatasetPaths,
) -> dict[str, Any]:
    source = _source_metadata(paths)
    latest_completed = runs.select(pl.col("ended_at").max()).item()
    earliest_started = runs.select(pl.col("started_at").min()).item()
    raw_cost_runs = runs.filter(pl.col("has_cost")).height
    positive_cost_runs = runs.filter(pl.col("has_positive_cost")).height
    runs_with_steps = runs.filter(pl.col("has_steps")).height
    total_runs = runs.height
    profile = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_version": METHODOLOGY_VERSION,
        "dataset_key": paths.key,
        "dataset_label": paths.label,
        "dataset_id": source.get("dataset_id", paths.dataset_id),
        "source_revision": source.get("revision"),
        "source_last_modified": source.get("last_modified"),
        "snapshot_cutoff": latest_completed.isoformat() if latest_completed else None,
        "earliest_started_at": earliest_started.isoformat() if earliest_started else None,
        "run_count": total_runs,
        "step_event_count": steps.height,
        "runs_with_usable_steps": runs_with_steps,
        "runs_without_usable_steps": total_runs - runs_with_steps,
        "trajectory_coverage": runs_with_steps / total_runs if total_runs else 0,
        "cost_field_coverage": raw_cost_runs / total_runs if total_runs else 0,
        "positive_cost_coverage": positive_cost_runs / total_runs if total_runs else 0,
        "zero_cost_count": runs.filter(pl.col("cost_status") == "zero").height,
        "missing_cost_count": runs.filter(pl.col("cost_status") == "missing").height,
        "duration_coverage": runs.filter(pl.col("has_duration")).height / total_runs
        if total_runs
        else 0,
        "token_coverage": runs.filter(pl.col("has_tokens")).height / total_runs
        if total_runs
        else 0,
        "unique_tasks": runs.select(pl.col("task_name").n_unique()).item(),
        "unique_agents": runs.select(pl.col("agent").n_unique()).item(),
        "unique_models_raw": runs.select(pl.col("model_raw").n_unique()).item(),
        "unique_models_canonical": runs.select(pl.col("model").n_unique()).item(),
        "run_id_sources": runs.group_by("run_id_source")
        .agg(pl.len().alias("runs"))
        .sort("runs", descending=True)
        .to_dicts(),
    }
    return profile


def _write_profile_markdown(profile: dict[str, Any], paths: DatasetPaths) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {paths.label} Data Profile",
        "",
        f"Generated from the local normalized {paths.label} snapshot.",
        "",
        f"- Generated at: `{profile['generated_at']}`",
        f"- Dataset revision: `{profile.get('source_revision')}`",
        f"- Snapshot cutoff: `{profile.get('snapshot_cutoff')}`",
        f"- Runs: `{profile['run_count']:,}`",
        f"- Step events: `{profile['step_event_count']:,}`",
        f"- Trajectory coverage: `{profile['trajectory_coverage']:.2%}`",
        f"- Cost field coverage: `{profile['cost_field_coverage']:.2%}`",
        f"- Positive cost coverage: `{profile['positive_cost_coverage']:.2%}`",
        f"- Token coverage: `{profile['token_coverage']:.2%}`",
        "",
        "Counts are generated artifacts, not permanent upstream facts.",
    ]
    (DOCS_DIR / paths.docs_profile_name).write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="terminalbench")
    args = parser.parse_args()
    paths = dataset_paths(args.dataset)

    runs = pl.read_parquet(paths.runs_path)
    steps = pl.read_parquet(paths.steps_path)
    failures = _failures(runs, steps)
    profile = _quality_profile(runs, steps, paths)

    paths.data_quality_path.parent.mkdir(parents=True, exist_ok=True)
    paths.data_quality_path.write_text(
        json.dumps(profile, indent=2, default=str) + "\n"
    )
    _write_profile_markdown(profile, paths)

    if failures:
        print("Validation failed")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("Validation passed")
    print(f"Runs: {profile['run_count']:,}")
    print(f"Step events: {profile['step_event_count']:,}")
    print(f"Data quality report: {paths.data_quality_path}")
    print(f"Data profile: {DOCS_DIR / paths.docs_profile_name}")


if __name__ == "__main__":
    main()
