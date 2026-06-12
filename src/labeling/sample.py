from __future__ import annotations

import argparse

import polars as pl

from src.common.constants import LABELS_DIR, RUNS_WITH_RCA_PATH


LABEL_COLUMNS = [
    "run_id",
    "primary_rca",
    "secondary_rca",
    "waste_types",
    "first_problem_step",
    "evidence_steps",
    "avoidable",
    "severity",
    "confidence",
    "notes",
    "reviewer",
    "reviewed_at",
]


def _take(df: pl.DataFrame, n: int, seed: int) -> pl.DataFrame:
    if df.height <= n:
        return df
    return df.sample(n=n, seed=seed, shuffle=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    runs = pl.read_parquet(RUNS_WITH_RCA_PATH)
    threshold = runs.select(pl.col("suspected_waste_rate").quantile(0.75)).item() or 0
    high_waste = pl.col("suspected_waste_rate") >= threshold
    failed = pl.col("success") == False  # noqa: E712
    successful = pl.col("success") == True  # noqa: E712

    bucket_specs = [
        ("failed_high_waste", runs.filter(failed & high_waste), 15),
        ("failed_low_waste", runs.filter(failed & ~high_waste), 10),
        ("successful_high_waste", runs.filter(successful & high_waste), 10),
        ("successful_low_waste", runs.filter(successful & ~high_waste), 10),
        (
            "outliers",
            runs.sort(["observed_tool_events", "suspected_waste_rate"], descending=True),
            5,
        ),
    ]

    frames: list[pl.DataFrame] = []
    for bucket, bucket_df, requested in bucket_specs:
        scaled = max(1, round(requested * args.size / 50))
        frames.append(_take(bucket_df, scaled, args.seed).with_columns(pl.lit(bucket).alias("bucket")))

    sample = pl.concat(frames, how="diagonal").unique("run_id").head(args.size)
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    output = LABELS_DIR / "labeling_sample.csv"
    sample.select(
        [
            "bucket",
            "run_id",
            "task_name",
            "agent",
            "model",
            "success",
            "rule_based_rca",
            "suspected_waste_rate",
            "error_event_rate",
            "observed_tool_events",
        ]
    ).write_csv(output)

    labels_path = LABELS_DIR / "rca_labels.csv"
    if not labels_path.exists():
        pl.DataFrame(schema={column: pl.String for column in LABEL_COLUMNS}).write_csv(
            labels_path
        )

    print(f"Labeling sample saved to {output}")
    print(f"Label template saved to {labels_path}")


if __name__ == "__main__":
    main()
