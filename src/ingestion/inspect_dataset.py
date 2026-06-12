from __future__ import annotations

import json
from typing import Any

import polars as pl

from src.common.constants import RAW_TERMINALBENCH_PATH
from src.common.numeric import to_float
from src.common.timestamps import parse_timestamp


def has_trajectory(value: Any) -> bool:
    if not value:
        return False

    try:
        parsed = json.loads(value)
        return isinstance(parsed, list) and len(parsed) > 0
    except (json.JSONDecodeError, TypeError):
        return False


def finite_number(value: Any) -> bool:
    return to_float(value) is not None


def main() -> None:
    df = pl.read_parquet(RAW_TERMINALBENCH_PATH)

    df = df.with_columns(
        pl.col("steps")
        .map_elements(
            has_trajectory,
            return_dtype=pl.Boolean,
        )
        .alias("has_trajectory")
    )

    total_rows = df.height
    print(f"Total rows: {total_rows:,}")

    print("\nSchema:")
    print(df.schema)

    parsed_starts = [parse_timestamp(value) for value in df.get_column("started_at")]
    parsed_ends = [parse_timestamp(value) for value in df.get_column("ended_at")]
    valid_starts = [value for value in parsed_starts if value is not None]
    valid_ends = [value for value in parsed_ends if value is not None]

    profile = df.select(
        pl.len().alias("total_runs"),
        pl.col("task_name").n_unique().alias("unique_tasks"),
        pl.col("agent").n_unique().alias("unique_agents"),
        pl.col("model").n_unique().alias("unique_models"),
        pl.col("has_trajectory").mean().alias("trajectory_coverage"),
        pl.col("cost_cents").map_elements(finite_number, return_dtype=pl.Boolean)
        .mean()
        .alias("cost_field_coverage"),
        (pl.col("cost_cents").map_elements(to_float, return_dtype=pl.Float64) > 0)
        .sum()
        .alias("positive_cost_count"),
        (pl.col("cost_cents").map_elements(to_float, return_dtype=pl.Float64) == 0)
        .sum()
        .alias("zero_cost_count"),
        pl.col("cost_cents")
        .map_elements(lambda value: to_float(value) is None, return_dtype=pl.Boolean)
        .sum()
        .alias("missing_or_nonfinite_cost_count"),
        pl.col("duration_seconds")
        .map_elements(finite_number, return_dtype=pl.Boolean)
        .mean()
        .alias("duration_coverage"),
        pl.any_horizontal(
            pl.col("input_tokens").map_elements(finite_number, return_dtype=pl.Boolean),
            pl.col("output_tokens").map_elements(finite_number, return_dtype=pl.Boolean),
            pl.col("cache_tokens").map_elements(finite_number, return_dtype=pl.Boolean),
        )
        .mean()
        .alias("token_coverage"),
        pl.col("trial_id").is_null().sum().alias("null_trial_id_count"),
        (pl.col("trial_id").str.strip_chars() == "").sum().alias("blank_trial_id_count"),
        pl.col("trial_id").is_duplicated().sum().alias("duplicate_trial_id_rows"),
    )

    print("\nProfile:")
    print(profile)
    print(f"Earliest valid timestamp: {min(valid_starts) if valid_starts else None}")
    print(f"Latest valid timestamp:   {max(valid_ends) if valid_ends else None}")

    print("\nTrajectory availability:")
    print(
        df.group_by("has_trajectory")
        .agg(pl.len().alias("runs"))
        .sort("has_trajectory", descending=True)
    )

    print("\nSuccess by trajectory availability:")
    print(
        df.group_by("has_trajectory")
        .agg(
            pl.len().alias("runs"),
            pl.col("reward").mean().alias("pass_rate"),
            pl.col("cost_cents").median().alias("median_cost_cents"),
            pl.col("duration_seconds")
            .median()
            .alias("median_duration_seconds"),
        )
        .sort("has_trajectory", descending=True)
    )

    print("\nTop agent/model combinations:")
    print(
        df.group_by(["agent", "model"])
        .agg(
            pl.len().alias("runs"),
            pl.col("reward").mean().alias("pass_rate"),
            pl.col("has_trajectory")
            .mean()
            .alias("trajectory_coverage"),
            pl.col("cost_cents").median().alias("median_cost_cents"),
        )
        .sort("runs", descending=True)
        .head(20)
    )


if __name__ == "__main__":
    main()
