from __future__ import annotations

import argparse
import json
from typing import Any

import duckdb
import polars as pl

from src.benchmarks.metrics import cost_metrics_eligible, safe_divide, wilson_interval
from src.common.constants import (
    BENCHMARK_VERSION,
    METHODOLOGY_VERSION,
)
from src.common.datasets import DatasetPaths, dataset_paths


PUBLIC_RANKED_MIN_RUNS = 100
INTERNAL_MIN_RUNS = 20


def _register_table(con: duckdb.DuckDBPyConnection, name: str, df: pl.DataFrame) -> None:
    con.register("_tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM _tmp_df")
    con.unregister("_tmp_df")


def _overview(df: pl.DataFrame) -> pl.DataFrame:
    total = df.height
    with_trajectories = df.filter(pl.col("has_steps")).height
    costs = df.filter(pl.col("has_cost")).height
    positives = df.filter(pl.col("has_positive_cost")).height
    latest_ended = df.select(pl.col("ended_at").max()).item()
    estimated_wasted_cost = (
        df.select(pl.col("estimated_wasted_cost_usd").sum()).item()
        if costs
        else None
    )
    overview = {
        "benchmark_version": BENCHMARK_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "dataset_key": df.select(pl.col("source_dataset").drop_nulls().first()).item(),
        "dataset_revision": df.select(pl.col("source_revision").drop_nulls().first()).item(),
        "snapshot_cutoff": str(latest_ended) if latest_ended is not None else None,
        "runs": total,
        "runs_with_trajectories": with_trajectories,
        "trajectory_coverage": safe_divide(with_trajectories, total),
        "pass_rate": df.select(pl.col("success").mean()).item() or 0,
        "tasks": df.select(pl.col("task_name").n_unique()).item(),
        "agents": df.select(pl.col("agent").n_unique()).item(),
        "models": df.select(pl.col("model").n_unique()).item(),
        "cost_field_coverage": safe_divide(costs, total),
        "positive_cost_coverage": safe_divide(positives, total),
        "median_duration_seconds": df.select(pl.col("duration_seconds").median()).item(),
        "median_steps": df.select(pl.col("step_count").median()).item(),
        "median_tool_calls": df.select(pl.col("tool_call_count").median()).item(),
        "mean_suspected_waste_rate": df.filter(pl.col("has_steps"))
        .select(pl.col("suspected_waste_rate").mean())
        .item()
        or 0,
        "estimated_wasted_cost_usd": estimated_wasted_cost,
        "estimated_wasted_duration_seconds": df.select(
            pl.col("estimated_wasted_duration_seconds").sum()
        ).item(),
    }
    return pl.DataFrame([overview])


def _macro_by_task(df: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    return (
        df.group_by(keys + ["task_name"])
        .agg(pl.col("success").mean().alias("_task_pass_rate"))
        .group_by(keys)
        .agg(pl.col("_task_pass_rate").mean().alias("pass_rate_macro_by_task"))
    )


def _leaderboard(df: pl.DataFrame, keys: list[str], uncontrolled: bool = False) -> pl.DataFrame:
    grouped = df.group_by(keys).agg(
        pl.len().alias("runs"),
        pl.col("task_name").n_unique().alias("tasks"),
        pl.col("success").sum().alias("successful_runs"),
        pl.col("success").mean().alias("pass_rate_micro"),
        pl.col("duration_seconds").median().alias("median_duration_seconds"),
        pl.col("step_count").median().alias("median_steps"),
        pl.col("tool_call_count").median().alias("median_tool_calls"),
        pl.col("has_steps").mean().alias("trajectory_coverage"),
        pl.col("has_cost").mean().alias("cost_field_coverage"),
        pl.col("has_positive_cost").mean().alias("positive_cost_coverage"),
        pl.col("cost_usd").filter(pl.col("has_positive_cost")).median().alias("median_positive_cost_usd"),
        pl.col("cost_usd").filter(pl.col("has_cost")).sum().alias("_observed_cost_sum"),
        (pl.col("success") & pl.col("has_cost")).sum().alias("_successful_usable_cost_runs"),
        pl.col("suspected_waste_rate").mean().alias("mean_suspected_waste_rate"),
        pl.col("error_event_rate").mean().alias("mean_error_event_rate"),
        pl.col("repeat_rate").mean().alias("mean_repeat_rate"),
        pl.col("possible_missing_verification").mean().alias("missing_verification_rate"),
        pl.col("source_revision").drop_nulls().first().alias("dataset_revision"),
        pl.col("ended_at").max().cast(pl.String).alias("snapshot_cutoff"),
    )
    macro = _macro_by_task(df, keys)
    rows: list[dict[str, Any]] = []
    for row in grouped.join(macro, on=keys, how="left").iter_rows(named=True):
        low, high = wilson_interval(int(row["successful_runs"]), int(row["runs"]))
        row["pass_rate_wilson_low"] = low
        row["pass_rate_wilson_high"] = high
        row["cost_metrics_eligible"] = cost_metrics_eligible(
            int(row["runs"]),
            float(row["positive_cost_coverage"] or 0),
            min_runs=INTERNAL_MIN_RUNS,
        )
        row["public_rank_eligible"] = int(row["runs"]) >= PUBLIC_RANKED_MIN_RUNS
        row["observed_cost_per_success_usd"] = (
            safe_divide(row["_observed_cost_sum"], row["_successful_usable_cost_runs"])
            if row["cost_metrics_eligible"]
            else None
        )
        if uncontrolled:
            row["comparison_scope"] = "uncontrolled_historical_model_summary"
        rows.append(row)
    return pl.DataFrame(rows, strict=False).drop(
        ["_observed_cost_sum", "_successful_usable_cost_runs"], strict=False
    )


def _task_difficulty(df: pl.DataFrame) -> pl.DataFrame:
    return df.group_by("task_name").agg(
        pl.len().alias("runs"),
        pl.col("agent").n_unique().alias("agents"),
        pl.col("model").n_unique().alias("models"),
        pl.col("success").mean().alias("pass_rate"),
        pl.col("duration_seconds").median().alias("median_duration_seconds"),
        pl.col("step_count").median().alias("median_steps"),
        pl.col("suspected_waste_rate").mean().alias("mean_suspected_waste_rate"),
    )


def _outcome_comparison(df: pl.DataFrame) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for scope, scoped in (
        ("all_runs", df),
        ("trajectory_only", df.filter(pl.col("has_steps"))),
    ):
        if scoped.is_empty():
            continue
        frames.append(
            scoped.with_columns(pl.lit(scope).alias("scope"))
            .group_by(["scope", "success"])
            .agg(
                pl.len().alias("runs"),
                pl.col("cost_usd").filter(pl.col("has_cost")).median().alias("median_cost_usd"),
                pl.col("duration_seconds").median().alias("median_duration_seconds"),
                pl.col("step_count").median().alias("median_steps"),
                pl.col("tool_call_count").median().alias("median_tool_calls"),
                pl.col("suspected_waste_rate").mean().alias("mean_suspected_waste_rate"),
                pl.col("error_event_rate").mean().alias("mean_error_event_rate"),
                pl.col("repeat_rate").mean().alias("mean_repeat_rate"),
            )
        )
    return pl.concat(frames, how="diagonal")


def _failure_patterns(df: pl.DataFrame) -> pl.DataFrame:
    return df.group_by("rule_based_rca").agg(
        pl.len().alias("runs"),
        (pl.col("success") == False).sum().alias("failed_runs"),  # noqa: E712
        pl.col("suspected_waste_rate").mean().alias("mean_suspected_waste_rate"),
        pl.col("estimated_wasted_cost_usd").sum().alias("estimated_wasted_cost_usd"),
        pl.col("rca_confidence").mean().alias("mean_rca_confidence"),
    )


def _coverage(df: pl.DataFrame, column: str) -> pl.DataFrame:
    return df.group_by(["agent", "model"]).agg(
        pl.len().alias("runs"),
        pl.col(column).mean().alias("coverage"),
        pl.col("source_revision").drop_nulls().first().alias("dataset_revision"),
        pl.col("ended_at").max().cast(pl.String).alias("snapshot_cutoff"),
    )


def _data_quality_df(paths: DatasetPaths) -> pl.DataFrame:
    if not paths.data_quality_path.exists():
        return pl.DataFrame([{"data_quality_json": "{}"}])
    return pl.DataFrame([{"data_quality_json": paths.data_quality_path.read_text()}])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="terminalbench")
    args = parser.parse_args()
    paths = dataset_paths(args.dataset)

    paths.benchmark_db_path.parent.mkdir(parents=True, exist_ok=True)
    if paths.benchmark_db_path.exists():
        paths.benchmark_db_path.unlink()

    con = duckdb.connect(str(paths.benchmark_db_path))
    con.execute(
        f"CREATE TABLE runs AS SELECT * FROM read_parquet('{paths.runs_path.as_posix()}')"
    )
    con.execute(
        f"CREATE TABLE steps AS SELECT * FROM read_parquet('{paths.steps_path.as_posix()}')"
    )
    con.execute(
        "CREATE TABLE step_signals AS "
        f"SELECT * FROM read_parquet('{paths.step_signals_path.as_posix()}')"
    )
    con.execute(
        "CREATE TABLE run_signals AS "
        f"SELECT * FROM read_parquet('{paths.run_signals_path.as_posix()}')"
    )
    con.execute(
        "CREATE TABLE runs_with_rca AS "
        f"SELECT * FROM read_parquet('{paths.runs_with_rca_path.as_posix()}')"
    )

    df = pl.read_parquet(paths.runs_with_rca_path)
    tables = {
        "overview": _overview(df),
        "data_quality": _data_quality_df(paths),
        "agent_model_leaderboard": _leaderboard(df, ["agent", "model"]),
        "agent_leaderboard": _leaderboard(df, ["agent"]),
        "model_uncontrolled_leaderboard": _leaderboard(df, ["model"], uncontrolled=True),
        "task_difficulty": _task_difficulty(df),
        "outcome_comparison": _outcome_comparison(df),
        "failure_patterns": _failure_patterns(df),
        "cost_coverage_by_system": _coverage(df, "has_cost"),
        "trajectory_coverage_by_system": _coverage(df, "has_steps"),
    }
    for name, table_df in tables.items():
        _register_table(con, name, table_df)

    con.close()
    artifact_summary = {
        "database": str(paths.benchmark_db_path),
        "tables": ["runs", "steps", "step_signals", "run_signals", "runs_with_rca"]
        + list(tables),
    }
    print(json.dumps(artifact_summary, indent=2))


if __name__ == "__main__":
    main()
