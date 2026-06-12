from __future__ import annotations

import argparse

import polars as pl

from src.common.datasets import dataset_paths


COUNT_COLUMNS = [
    "observed_tool_events",
    "error_events",
    "test_actions",
    "edit_actions",
    "read_actions",
    "search_actions",
    "shell_actions",
    "submission_actions",
    "adjacent_repeats",
    "same_result_repeats",
    "repeated_failed_attempts",
    "suspected_wasted_actions",
]

RATE_COLUMNS = [
    "suspected_waste_rate",
    "error_event_rate",
    "repeat_rate",
    "read_search_rate",
]


def _rate(numerator: str, denominator: str = "observed_tool_events") -> pl.Expr:
    return (
        pl.when(pl.col(denominator) > 0)
        .then(pl.col(numerator) / pl.col(denominator))
        .otherwise(0.0)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="terminalbench")
    args = parser.parse_args()
    paths = dataset_paths(args.dataset)

    signals = pl.scan_parquet(paths.step_signals_path)
    tool_events = signals.filter(pl.col("normalized_action") != "")

    grouped = tool_events.group_by("run_id").agg(
        pl.len().cast(pl.Int64).alias("observed_tool_events"),
        pl.col("is_error").sum().cast(pl.Int64).alias("error_events"),
        pl.col("is_test").sum().cast(pl.Int64).alias("test_actions"),
        pl.col("is_edit").sum().cast(pl.Int64).alias("edit_actions"),
        pl.col("is_read").sum().cast(pl.Int64).alias("read_actions"),
        pl.col("is_search").sum().cast(pl.Int64).alias("search_actions"),
        pl.col("is_shell").sum().cast(pl.Int64).alias("shell_actions"),
        pl.col("is_submission").sum().cast(pl.Int64).alias("submission_actions"),
        pl.col("is_adjacent_repeat").sum().cast(pl.Int64).alias("adjacent_repeats"),
        pl.col("same_result_repeat").sum().cast(pl.Int64).alias("same_result_repeats"),
        pl.col("repeated_failed_attempt")
        .sum()
        .cast(pl.Int64)
        .alias("repeated_failed_attempts"),
        pl.col("suspected_waste")
        .sum()
        .cast(pl.Int64)
        .alias("suspected_wasted_actions"),
    )

    output = (
        pl.scan_parquet(paths.runs_path)
        .join(grouped, on="run_id", how="left")
        .with_columns(pl.col(COUNT_COLUMNS).fill_null(0))
        .with_columns(
            _rate("suspected_wasted_actions").alias("suspected_waste_rate"),
            _rate("error_events").alias("error_event_rate"),
            _rate("adjacent_repeats").alias("repeat_rate"),
            (
                pl.when(pl.col("observed_tool_events") > 0)
                .then(
                    (pl.col("read_actions") + pl.col("search_actions"))
                    / pl.col("observed_tool_events")
                )
                .otherwise(0.0)
            ).alias("read_search_rate"),
            (
                (pl.col("edit_actions") > 0) & (pl.col("test_actions") == 0)
            ).alias("possible_missing_verification"),
        )
        .with_columns(
            (
                pl.when(pl.col("has_cost") & (pl.col("observed_tool_events") > 0))
                .then(pl.col("cost_usd") * pl.col("suspected_waste_rate"))
                .otherwise(None)
            ).alias("estimated_wasted_cost_usd"),
            (
                pl.when(pl.col("has_duration") & (pl.col("observed_tool_events") > 0))
                .then(
                    pl.col("duration_seconds") * pl.col("suspected_waste_rate")
                )
                .otherwise(None)
            ).alias("estimated_wasted_duration_seconds"),
        )
        .with_columns(pl.col(RATE_COLUMNS).cast(pl.Float64))
    )

    paths.run_signals_path.parent.mkdir(parents=True, exist_ok=True)
    output.sink_parquet(paths.run_signals_path, compression="zstd")
    row_count = pl.scan_parquet(paths.run_signals_path).select(pl.len()).collect().item()
    print(f"Aggregated {row_count:,} runs")
    print(f"Run signals saved to {paths.run_signals_path}")


if __name__ == "__main__":
    main()
