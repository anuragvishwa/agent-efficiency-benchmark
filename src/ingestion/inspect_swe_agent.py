from __future__ import annotations

import polars as pl

from src.common.datasets import dataset_paths


def main() -> None:
    paths = dataset_paths("swe_agent")
    if not paths.raw_path.exists():
        raise FileNotFoundError(
            f"SWE-agent dataset not found at {paths.raw_path}. "
            "Run python -m src.ingestion.download_swe_agent first."
        )

    lf = pl.scan_parquet(paths.raw_path)
    schema = lf.collect_schema()
    print(f"Total rows: {lf.select(pl.len()).collect().item():,}")
    print("\nSchema:")
    print(schema)

    profile = lf.select(
        pl.len().alias("total_runs"),
        pl.col("instance_id").n_unique().alias("unique_instances"),
        pl.col("model_name").n_unique().alias("unique_models"),
        pl.col("target").mean().alias("success_rate"),
        pl.col("trajectory").list.len().mean().alias("mean_trajectory_turns"),
        pl.col("trajectory").list.len().median().alias("median_trajectory_turns"),
        (pl.col("trajectory").list.len() > 0).mean().alias("trajectory_coverage"),
        pl.col("generated_patch").str.len_chars().mean().alias("mean_patch_chars"),
        pl.col("eval_logs").str.len_chars().mean().alias("mean_eval_log_chars"),
    ).collect()

    print("\nProfile:")
    print(profile)

    print("\nModels:")
    print(
        lf.group_by("model_name")
        .agg(
            pl.len().alias("runs"),
            pl.col("target").mean().alias("pass_rate"),
            pl.col("trajectory").list.len().median().alias("median_trajectory_turns"),
        )
        .sort("runs", descending=True)
        .collect()
    )

    print("\nExit statuses:")
    print(
        lf.group_by("exit_status")
        .agg(pl.len().alias("runs"), pl.col("target").mean().alias("pass_rate"))
        .sort("runs", descending=True)
        .collect()
    )


if __name__ == "__main__":
    main()
