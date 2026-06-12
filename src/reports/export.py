from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import polars as pl

from src.common.constants import (
    BENCHMARK_VERSION,
    METHODOLOGY_VERSION,
    REPORTS_DIR,
)
from src.common.datasets import DATASETS, DatasetPaths
from src.reports.sanitize import sanitize_text
from src.reports.schemas import PublicBenchmark


TERMINAL_CSV_TABLES = {
    "agent_model_leaderboard": "leaderboard_agent_model.csv",
    "agent_leaderboard": "leaderboard_agent.csv",
    "model_uncontrolled_leaderboard": "leaderboard_model_uncontrolled.csv",
    "outcome_comparison": "outcome_comparison.csv",
    "task_difficulty": "task_difficulty.csv",
    "failure_patterns": "failure_patterns.csv",
}

SWE_CSV_TABLES = {
    "model_uncontrolled_leaderboard": "swe_agent_model_leaderboard.csv",
    "outcome_comparison": "swe_agent_outcome_comparison.csv",
    "failure_patterns": "swe_agent_failure_patterns.csv",
}


def _query(con: duckdb.DuckDBPyConnection, sql: str) -> pl.DataFrame:
    return pl.from_arrow(con.execute(sql).to_arrow_table())


def _git_metadata() -> dict[str, Any]:
    def run_git(args: list[str]) -> str | None:
        try:
            return subprocess.check_output(
                ["git", *args], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    commit = run_git(["rev-parse", "HEAD"])
    status = run_git(["status", "--short"])
    return {
        "code_commit": commit or "not_git_repository",
        "dirty_status": bool(status) if status is not None else None,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")


def _early_stopping(paths: DatasetPaths) -> list[dict[str, Any]]:
    if not paths.early_stop_path.exists():
        return []
    return (
        pl.read_parquet(paths.early_stop_path)
        .group_by("policy")
        .agg(
            pl.len().alias("runs"),
            pl.col("triggered").mean().alias("trigger_rate"),
            pl.col("false_stop").mean().alias("false_stop_rate"),
            pl.col("events_saved").sum().alias("events_saved"),
            pl.col("estimated_cost_saved_usd").sum().alias("estimated_cost_saved_usd"),
            pl.col("estimated_duration_saved_seconds")
            .sum()
            .alias("estimated_duration_saved_seconds"),
            pl.col("estimate_label").first().alias("estimate_label"),
        )
        .sort("policy")
        .to_dicts()
    )


def _selected_examples(paths: DatasetPaths, output_name: str) -> list[dict[str, Any]]:
    runs = (
        pl.read_parquet(paths.runs_with_rca_path)
        .sort(
            ["suspected_waste_rate", "error_event_rate", "observed_tool_events"],
            descending=[True, True, True],
        )
        .head(12)
    )
    run_ids = runs.get_column("run_id").to_list()
    if not run_ids:
        examples: list[dict[str, Any]] = []
        _write_json(REPORTS_DIR / "examples" / output_name, examples)
        return examples

    steps = (
        pl.scan_parquet(paths.step_signals_path)
        .filter(pl.col("run_id").is_in(run_ids))
        .select(
            [
                "run_id",
                "step_index",
                "tool_index",
                "source",
                "message",
                "tool_name",
                "command",
                "observation",
                "is_error",
                "suspected_waste",
                "repeated_failed_attempt",
            ]
        )
        .sort(["run_id", "step_index", "tool_index"])
        .collect()
    )
    examples: list[dict[str, Any]] = []
    for run in runs.iter_rows(named=True):
        run_steps = steps.filter(pl.col("run_id") == run["run_id"]).head(40)
        examples.append(
            {
                "dataset": paths.key,
                "run_id": run["run_id"],
                "task_name": run["task_name"],
                "agent": run["agent"],
                "model": run["model"],
                "success": run["success"],
                "rule_based_rca": run["rule_based_rca"],
                "suspected_waste_rate": run["suspected_waste_rate"],
                "trajectory_backed": bool(run["has_steps"]),
                "steps": [
                    {
                        key: sanitize_text(value) if isinstance(value, str) else value
                        for key, value in step.items()
                    }
                    for step in run_steps.to_dicts()
                ],
            }
        )
    _write_json(REPORTS_DIR / "examples" / output_name, examples)
    return examples


def _metadata(paths: DatasetPaths, overview: dict[str, Any]) -> dict[str, Any]:
    data_quality = (
        json.loads(paths.data_quality_path.read_text())
        if paths.data_quality_path.exists()
        else {}
    )
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_key": paths.key,
        "dataset_label": paths.label,
        "dataset_id": data_quality.get("dataset_id", paths.dataset_id),
        "dataset_revision": overview.get("dataset_revision"),
        "snapshot_cutoff": overview.get("snapshot_cutoff"),
        "run_count": overview.get("runs"),
        **_git_metadata(),
    }


def _coverage(overview: dict[str, Any]) -> dict[str, Any]:
    return {
        "trajectory_coverage": overview.get("trajectory_coverage"),
        "cost_field_coverage": overview.get("cost_field_coverage"),
        "positive_cost_coverage": overview.get("positive_cost_coverage"),
        "dataset_revision": overview.get("dataset_revision"),
        "snapshot_cutoff": overview.get("snapshot_cutoff"),
    }


def _dataset_payload(paths: DatasetPaths) -> dict[str, Any]:
    con = duckdb.connect(str(paths.benchmark_db_path))
    overview = _query(con, "SELECT * FROM overview").to_dicts()[0]
    systems = _query(
        con,
        "SELECT * FROM agent_model_leaderboard "
        "ORDER BY public_rank_eligible DESC, pass_rate_micro DESC, runs DESC",
    )
    agents = _query(
        con,
        "SELECT * FROM agent_leaderboard "
        "ORDER BY public_rank_eligible DESC, pass_rate_micro DESC, runs DESC",
    )
    models = _query(
        con,
        "SELECT * FROM model_uncontrolled_leaderboard "
        "ORDER BY public_rank_eligible DESC, pass_rate_micro DESC, runs DESC",
    )
    tasks = _query(con, "SELECT * FROM task_difficulty ORDER BY runs DESC")
    failures = _query(con, "SELECT * FROM failure_patterns ORDER BY failed_runs DESC")
    con.close()

    examples_name = (
        "selected_trajectories.json"
        if paths.key == "terminalbench"
        else f"{paths.report_prefix}selected_trajectories.json"
    )
    examples = _selected_examples(paths, examples_name)
    return {
        "metadata": _metadata(paths, overview),
        "coverage": _coverage(overview),
        "overview": overview,
        "systems": systems.to_dicts(),
        "agents": agents.to_dicts(),
        "models_uncontrolled": models.to_dicts(),
        "tasks": tasks.to_dicts(),
        "failure_patterns": failures.to_dicts(),
        "early_stopping": _early_stopping(paths),
        "examples": examples,
    }


def _export_dataset_reports(paths: DatasetPaths, payload: dict[str, Any]) -> None:
    con = duckdb.connect(str(paths.benchmark_db_path))
    if paths.key == "terminalbench":
        _write_json(REPORTS_DIR / "overview.json", payload["overview"])
        for table, filename in TERMINAL_CSV_TABLES.items():
            _query(con, f"SELECT * FROM {table}").write_csv(REPORTS_DIR / filename)
        if paths.early_stop_path.exists():
            pl.read_parquet(paths.early_stop_path).write_csv(
                REPORTS_DIR / "early_stop_simulation.csv"
            )
    else:
        _write_json(REPORTS_DIR / f"{paths.report_prefix}overview.json", payload["overview"])
        for table, filename in SWE_CSV_TABLES.items():
            _query(con, f"SELECT * FROM {table}").write_csv(REPORTS_DIR / filename)
        if paths.early_stop_path.exists():
            pl.read_parquet(paths.early_stop_path).write_csv(
                REPORTS_DIR / f"{paths.report_prefix}early_stop_simulation.csv"
            )
        _write_json(
            REPORTS_DIR / f"{paths.report_prefix}public_benchmark.json",
            payload,
        )
    con.close()


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "examples").mkdir(parents=True, exist_ok=True)

    terminal_paths = DATASETS["terminalbench"]
    terminal_payload = _dataset_payload(terminal_paths)
    _export_dataset_reports(terminal_paths, terminal_payload)

    datasets = [terminal_payload]
    swe_paths = DATASETS["swe_agent"]
    if swe_paths.benchmark_db_path.exists():
        swe_payload = _dataset_payload(swe_paths)
        _export_dataset_reports(swe_paths, swe_payload)
        datasets.append(swe_payload)

    public_payload = {**terminal_payload, "datasets": datasets}
    PublicBenchmark.model_validate(public_payload)
    _write_json(REPORTS_DIR / "public_benchmark.json", public_payload)

    artifacts = sorted(
        str(path)
        for path in REPORTS_DIR.rglob("*")
        if path.is_file() and path.name != ".gitkeep"
    )
    manifest = {
        "metadata": public_payload["metadata"],
        "coverage": public_payload["coverage"],
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    _write_json(REPORTS_DIR / "manifest.json", manifest)

    print(f"Exported {len(artifacts):,} report artifacts")
    print(f"Public benchmark: {REPORTS_DIR / 'public_benchmark.json'}")
    if swe_paths.benchmark_db_path.exists():
        print(
            "SWE-agent public benchmark: "
            f"{REPORTS_DIR / 'swe_agent_public_benchmark.json'}"
        )


if __name__ == "__main__":
    main()
