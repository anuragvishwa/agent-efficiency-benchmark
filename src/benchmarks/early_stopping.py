from __future__ import annotations

import argparse
from collections.abc import Iterable
from typing import Any

import duckdb
import polars as pl

from src.common.constants import (
    REPORTS_DIR,
)
from src.common.datasets import dataset_paths


POLICIES = {
    "third_identical_failed_action_result": "Stop after the third identical failed action/result.",
    "five_consecutive_errors": "Stop after five consecutive error-like tool events.",
    "same_result_no_progress_burst": "Stop after a same-result no-progress burst.",
}


def _empty_trigger() -> dict[str, Any]:
    return {
        "triggered": False,
        "trigger_step_index": None,
        "trigger_event_number": None,
    }


def _finalize_run(
    run_id: str,
    triggers: dict[str, dict[str, Any]],
    run_meta: dict[str, dict[str, Any]],
) -> Iterable[dict[str, Any]]:
    meta = run_meta.get(run_id, {})
    observed = int(meta.get("observed_tool_events") or 0)
    success = bool(meta.get("success")) if meta.get("success") is not None else False
    cost = meta.get("cost_usd")
    duration = meta.get("duration_seconds")
    for policy, description in POLICIES.items():
        trigger = triggers.get(policy, _empty_trigger())
        trigger_event = trigger.get("trigger_event_number")
        events_saved = max(observed - int(trigger_event or observed), 0) if trigger["triggered"] else 0
        rate_saved = events_saved / observed if observed else 0
        yield {
            "run_id": run_id,
            "policy": policy,
            "policy_description": description,
            "triggered": trigger["triggered"],
            "trigger_step_index": trigger.get("trigger_step_index"),
            "trigger_event_number": trigger_event,
            "events_saved": events_saved,
            "proportional_events_saved": rate_saved,
            "estimated_cost_saved_usd": cost * rate_saved if cost is not None else None,
            "estimated_duration_saved_seconds": duration * rate_saved
            if duration is not None
            else None,
            "historical_success": success,
            "false_stop": bool(success and trigger["triggered"]),
            "estimate_label": "counterfactual_historical_estimate",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--burst", type=int, default=4)
    parser.add_argument("--dataset", default="terminalbench")
    args = parser.parse_args()
    paths = dataset_paths(args.dataset)

    run_meta = {
        row["run_id"]: row
        for row in pl.read_parquet(paths.run_signals_path).select(
            [
                "run_id",
                "success",
                "cost_usd",
                "duration_seconds",
                "observed_tool_events",
            ]
        ).iter_rows(named=True)
    }

    step_rows = (
        pl.scan_parquet(paths.step_signals_path)
        .filter(pl.col("normalized_action") != "")
        .select(
            [
                "run_id",
                "step_index",
                "normalized_action",
                "observation_key",
                "is_error",
                "is_edit",
            ]
        )
        .sort(["run_id", "step_index"])
        .collect()
    )

    results: list[dict[str, Any]] = []
    current_run: str | None = None
    triggers: dict[str, dict[str, Any]] = {}
    event_number = 0
    last_failed_pair: tuple[str, str] | None = None
    failed_pair_count = 0
    consecutive_errors = 0
    last_result_pair: tuple[str, str] | None = None
    result_pair_count = 0

    for row in step_rows.iter_rows(named=True):
        run_id = row["run_id"]
        if current_run is not None and run_id != current_run:
            results.extend(_finalize_run(current_run, triggers, run_meta))
            triggers = {}
            event_number = 0
            last_failed_pair = None
            failed_pair_count = 0
            consecutive_errors = 0
            last_result_pair = None
            result_pair_count = 0

        current_run = run_id
        event_number += 1
        pair = (row["normalized_action"], row["observation_key"])

        if row["is_error"]:
            consecutive_errors += 1
            if pair == last_failed_pair:
                failed_pair_count += 1
            else:
                failed_pair_count = 1
                last_failed_pair = pair
            if (
                failed_pair_count >= 3
                and "third_identical_failed_action_result" not in triggers
            ):
                triggers["third_identical_failed_action_result"] = {
                    "triggered": True,
                    "trigger_step_index": row["step_index"],
                    "trigger_event_number": event_number,
                }
            if consecutive_errors >= 5 and "five_consecutive_errors" not in triggers:
                triggers["five_consecutive_errors"] = {
                    "triggered": True,
                    "trigger_step_index": row["step_index"],
                    "trigger_event_number": event_number,
                }
        else:
            consecutive_errors = 0
            last_failed_pair = None
            failed_pair_count = 0

        if not row["is_edit"] and pair == last_result_pair:
            result_pair_count += 1
        else:
            result_pair_count = 1
            last_result_pair = pair
        if (
            result_pair_count >= args.burst
            and "same_result_no_progress_burst" not in triggers
        ):
            triggers["same_result_no_progress_burst"] = {
                "triggered": True,
                "trigger_step_index": row["step_index"],
                "trigger_event_number": event_number,
            }

    if current_run is not None:
        results.extend(_finalize_run(current_run, triggers, run_meta))

    # Include no-trajectory/no-tool runs as non-triggered rows.
    emitted = {row["run_id"] for row in results}
    for run_id in set(run_meta) - emitted:
        results.extend(_finalize_run(run_id, {}, run_meta))

    output = pl.DataFrame(results, strict=False)
    paths.early_stop_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_parquet(paths.early_stop_path, compression="zstd")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output.write_csv(REPORTS_DIR / f"{paths.report_prefix}early_stop_simulation.csv")

    if paths.benchmark_db_path.exists():
        con = duckdb.connect(str(paths.benchmark_db_path))
        con.register("_early_stop", output)
        con.execute(
            "CREATE OR REPLACE TABLE early_stop_simulation AS "
            "SELECT * FROM _early_stop"
        )
        con.close()

    aggregate = output.group_by("policy").agg(
        pl.len().alias("runs"),
        pl.col("triggered").mean().alias("trigger_rate"),
        pl.col("false_stop").mean().alias("false_stop_rate"),
        pl.col("events_saved").sum().alias("events_saved"),
        pl.col("estimated_cost_saved_usd").sum().alias("estimated_cost_saved_usd"),
        pl.col("estimated_duration_saved_seconds")
        .sum()
        .alias("estimated_duration_saved_seconds"),
    )
    print(aggregate)
    print(f"Early-stop simulation saved to {paths.early_stop_path}")


if __name__ == "__main__":
    main()
