from __future__ import annotations

import argparse

import polars as pl

from src.common.constants import RAW_TERMINALBENCH_PATH


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="append", required=True)
    args = parser.parse_args()

    df = pl.read_parquet(RAW_TERMINALBENCH_PATH)
    cutoff = df.select(pl.col("ended_at").str.to_datetime(strict=False).max()).item()
    print(f"Snapshot cutoff: {cutoff}")
    for model in args.model:
        subset = df.filter(pl.col("model") == model)
        print(f"\nModel: {model}")
        print(f"Exact matches: {subset.height:,}")
        if subset.is_empty():
            print("Trajectory unavailable in this dataset snapshot.")
            continue
        print(
            subset.group_by("agent")
            .agg(
                pl.len().alias("runs"),
                pl.col("task_name").n_unique().alias("tasks"),
                pl.col("ended_at").str.to_datetime(strict=False).max().alias("latest_run"),
            )
            .sort("runs", descending=True)
        )


if __name__ == "__main__":
    main()
