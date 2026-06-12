from __future__ import annotations

import argparse

import polars as pl

from src.common.datasets import dataset_paths
from src.signals.classifiers import (
    ERROR_PATTERNS,
    is_edit_action,
    is_read_action,
    is_search_action,
    is_shell_action,
    is_submission_action,
    is_test_action,
    matches_any,
    normalize_command,
    normalize_tool_name,
    normalized_action,
    observation_key,
)


SIGNAL_COLUMNS = [
    "run_id",
    "task_name",
    "step_index",
    "tool_index",
    "source",
    "message",
    "tool_name",
    "command",
    "observation",
    "normalized_tool_name",
    "normalized_command",
    "normalized_action",
    "observation_key",
    "is_error",
    "is_test",
    "is_edit",
    "is_read",
    "is_search",
    "is_shell",
    "is_submission",
    "is_adjacent_repeat",
    "same_result_repeat",
    "repeated_failed_attempt",
    "suspected_waste",
]


def _action_struct(row: dict[str, object]) -> str:
    return normalized_action(row.get("tool_name"), row.get("command"))


def _tool_command_struct(row: dict[str, object], classifier) -> bool:
    return classifier(row.get("tool_name"), row.get("command"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="terminalbench")
    args = parser.parse_args()
    paths = dataset_paths(args.dataset)

    lf = (
        pl.scan_parquet(paths.steps_path)
        .sort(["run_id", "step_index", "tool_index"], nulls_last=True)
        .with_columns(
            pl.col("tool_name")
            .map_elements(normalize_tool_name, return_dtype=pl.String)
            .alias("normalized_tool_name"),
            pl.col("command")
            .map_elements(normalize_command, return_dtype=pl.String)
            .alias("normalized_command"),
            pl.struct(["tool_name", "command"])
            .map_elements(_action_struct, return_dtype=pl.String)
            .alias("normalized_action"),
            pl.col("observation")
            .map_elements(observation_key, return_dtype=pl.String)
            .alias("observation_key"),
        )
        .with_columns(
            pl.col("observation")
            .map_elements(
                lambda value: matches_any(value, ERROR_PATTERNS),
                return_dtype=pl.Boolean,
            )
            .alias("is_error"),
            pl.struct(["tool_name", "command"])
            .map_elements(
                lambda row: _tool_command_struct(row, is_test_action),
                return_dtype=pl.Boolean,
            )
            .alias("is_test"),
            pl.struct(["tool_name", "command"])
            .map_elements(
                lambda row: _tool_command_struct(row, is_edit_action),
                return_dtype=pl.Boolean,
            )
            .alias("is_edit"),
            pl.struct(["tool_name", "command"])
            .map_elements(
                lambda row: _tool_command_struct(row, is_read_action),
                return_dtype=pl.Boolean,
            )
            .alias("is_read"),
            pl.struct(["tool_name", "command"])
            .map_elements(
                lambda row: _tool_command_struct(row, is_search_action),
                return_dtype=pl.Boolean,
            )
            .alias("is_search"),
            pl.struct(["tool_name", "command"])
            .map_elements(
                lambda row: _tool_command_struct(row, is_shell_action),
                return_dtype=pl.Boolean,
            )
            .alias("is_shell"),
            pl.struct(["tool_name", "command"])
            .map_elements(
                lambda row: _tool_command_struct(row, is_submission_action),
                return_dtype=pl.Boolean,
            )
            .alias("is_submission"),
        )
        .with_columns((pl.col("normalized_action") != "").alias("_is_tool_event"))
        .with_columns(
            pl.col("normalized_action")
            .shift(1)
            .over("run_id")
            .alias("_previous_action"),
            pl.col("observation_key").shift(1).over("run_id").alias("_previous_obs"),
            pl.col("_is_tool_event")
            .shift(1)
            .over("run_id")
            .fill_null(False)
            .alias("_previous_is_tool_event"),
        )
        .with_columns(
            (
                pl.col("_is_tool_event")
                & pl.col("_previous_is_tool_event")
                & (pl.col("normalized_action") == pl.col("_previous_action"))
            ).alias("is_adjacent_repeat")
        )
        .with_columns(
            (
                pl.col("is_adjacent_repeat")
                & (pl.col("observation_key") == pl.col("_previous_obs"))
            ).alias("same_result_repeat")
        )
        .with_columns(
            (
                pl.col("same_result_repeat")
                & ~pl.col("is_edit")
                & pl.col("_is_tool_event")
            ).alias("suspected_waste")
        )
        .with_columns(
            (pl.col("suspected_waste") & pl.col("is_error")).alias(
                "repeated_failed_attempt"
            )
        )
        .select(SIGNAL_COLUMNS)
    )

    paths.step_signals_path.parent.mkdir(parents=True, exist_ok=True)
    lf.sink_parquet(paths.step_signals_path, compression="zstd")
    row_count = (
        pl.scan_parquet(paths.step_signals_path).select(pl.len()).collect().item()
    )
    print(f"Classified {row_count:,} step events")
    print(f"Step signals saved to {paths.step_signals_path}")


if __name__ == "__main__":
    main()
