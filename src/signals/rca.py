from __future__ import annotations

import argparse
import json
from typing import Any

import polars as pl

from src.common.datasets import dataset_paths


MIN_SUCCESSFUL_PEERS = 5


def _evidence_json(value: Any) -> str:
    if value is None:
        return "[]"
    if isinstance(value, list):
        return json.dumps(value[:10])
    return json.dumps([value])


def _classify(row: dict[str, Any]) -> tuple[str, float, str, str]:
    failed = row.get("success") is False
    has_steps = bool(row.get("has_steps"))
    enough_peers = (row.get("successful_peer_runs") or 0) >= MIN_SUCCESSFUL_PEERS
    excessive = bool(row.get("excessive_exploration"))

    if not has_steps:
        return (
            "MISSING_TRAJECTORY",
            0.9,
            "No usable trajectory was available for rule-based analysis.",
            "[]",
        )
    if not failed:
        return (
            "NO_MAJOR_RULE_BASED_FAILURE",
            0.4,
            "The historical run succeeded; no failure RCA is assigned.",
            "[]",
        )
    if (row.get("repeated_failed_attempts") or 0) > 0:
        return (
            "REPEATED_FAILED_APPROACH",
            0.8,
            "The trajectory repeats the same failed action and result.",
            _evidence_json(row.get("repeated_failed_evidence")),
        )
    if (row.get("error_events") or 0) >= 3 or (row.get("error_event_rate") or 0) >= 0.25:
        return (
            "TOOL_EXECUTION_FAILURE",
            0.7,
            "The trajectory contains multiple error-like tool observations.",
            _evidence_json(row.get("error_evidence")),
        )
    if bool(row.get("possible_missing_verification")):
        return (
            "POSSIBLE_MISSING_VERIFICATION",
            0.55,
            "Edits were observed without a recognized test or verification action.",
            "[]",
        )
    if enough_peers and excessive:
        return (
            "EXCESSIVE_EXPLORATION",
            0.55,
            "The failed run exceeded successful-peer exploration baselines.",
            "[]",
        )
    if enough_peers and bool(row.get("late_failure")):
        return (
            "LATE_FAILURE",
            0.45,
            "The failure occurred after a comparatively long trajectory.",
            "[]",
        )
    return (
        "UNCLASSIFIED_FAILURE",
        0.2,
        "No high-confidence rule matched this failed trajectory.",
        "[]",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="terminalbench")
    args = parser.parse_args()
    paths = dataset_paths(args.dataset)

    run_signals = pl.read_parquet(paths.run_signals_path)

    baselines = (
        run_signals.filter((pl.col("success") == True) & (pl.col("observed_tool_events") > 0))  # noqa: E712
        .group_by("task_name")
        .agg(
            pl.len().alias("successful_peer_runs"),
            pl.col("observed_tool_events")
            .median()
            .alias("successful_median_observed_tool_events"),
            pl.col("read_search_rate")
            .quantile(0.9, interpolation="nearest")
            .alias("successful_p90_read_search_rate"),
            pl.col("step_count")
            .quantile(0.9, interpolation="nearest")
            .alias("successful_p90_step_count"),
        )
    )

    evidence = (
        pl.scan_parquet(paths.step_signals_path)
        .filter(pl.col("normalized_action") != "")
        .group_by("run_id")
        .agg(
            pl.col("step_index")
            .filter(pl.col("repeated_failed_attempt"))
            .head(10)
            .alias("repeated_failed_evidence"),
            pl.col("step_index")
            .filter(pl.col("is_error"))
            .head(10)
            .alias("error_evidence"),
        )
        .collect()
    )

    enriched = (
        run_signals.join(baselines, on="task_name", how="left")
        .join(evidence, on="run_id", how="left")
        .with_columns(
            (
                (pl.col("success") == False)  # noqa: E712
                & (pl.col("successful_peer_runs") >= MIN_SUCCESSFUL_PEERS)
                & (
                    (
                        pl.col("observed_tool_events")
                        > pl.col("successful_median_observed_tool_events")
                    )
                    & (
                        (pl.col("read_search_rate") > pl.col("successful_p90_read_search_rate"))
                        | (pl.col("step_count") > pl.col("successful_p90_step_count"))
                    )
                )
            )
            .fill_null(False)
            .alias("excessive_exploration"),
            (
                (pl.col("success") == False)  # noqa: E712
                & (pl.col("successful_peer_runs") >= MIN_SUCCESSFUL_PEERS)
                & (pl.col("step_count") >= pl.col("successful_p90_step_count"))
            )
            .fill_null(False)
            .alias("late_failure"),
        )
    )

    rows: list[dict[str, Any]] = []
    for row in enriched.iter_rows(named=True):
        category, confidence, explanation, evidence_json = _classify(row)
        row["rule_based_rca"] = category
        row["rca_confidence"] = confidence
        row["rca_explanation"] = explanation
        row["rca_evidence_step_indexes"] = evidence_json
        rows.append(row)

    output = pl.DataFrame(rows, strict=False)
    paths.runs_with_rca_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_parquet(paths.runs_with_rca_path, compression="zstd")
    print(f"Rule-based RCA saved to {paths.runs_with_rca_path}")
    print(f"Runs classified: {output.height:,}")


if __name__ == "__main__":
    main()
