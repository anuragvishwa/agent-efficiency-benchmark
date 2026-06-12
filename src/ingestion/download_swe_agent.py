from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset
from huggingface_hub import HfApi

from src.common.constants import RAW_SWE_AGENT_PATH, SWE_AGENT_DATASET_ID
from src.common.datasets import dataset_paths


def _metadata_from_values(
    row_count: int,
    columns: list[str],
    output_path: Path,
) -> dict[str, object]:
    info = HfApi().dataset_info(SWE_AGENT_DATASET_ID)
    return {
        "dataset_id": SWE_AGENT_DATASET_ID,
        "revision": getattr(info, "sha", None),
        "last_modified": (
            info.last_modified.isoformat() if getattr(info, "last_modified", None) else None
        ),
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "split": "train",
        "row_count": row_count,
        "columns": columns,
        "local_file": str(output_path),
        "local_file_size": output_path.stat().st_size,
        "license": "cc-by-4.0",
        "license_notes": (
            "Respect licenses of each underlying repository; dataset card also "
            "notes Llama 3.1 license obligations for model outputs."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional local smoke-test limit. Full dataset is used by default.",
    )
    args = parser.parse_args()

    paths = dataset_paths("swe_agent")
    paths.raw_path.parent.mkdir(parents=True, exist_ok=True)
    if paths.raw_path.exists() and not args.force:
        raise SystemExit(
            f"{paths.raw_path} already exists. Re-run with --force to overwrite."
        )

    if args.limit is not None:
        stream = load_dataset(SWE_AGENT_DATASET_ID, split="train", streaming=True)
        rows = []
        for index, row in enumerate(stream):
            if index >= args.limit:
                break
            rows.append(row)
        if not rows:
            raise SystemExit("No SWE-agent rows were streamed")
        table = pa.Table.from_pylist(rows)
        tmp_path = RAW_SWE_AGENT_PATH.with_suffix(".parquet.tmp")
        pq.write_table(table, tmp_path, compression="zstd")
        tmp_path.replace(paths.raw_path)
        row_count = len(rows)
        columns = list(table.column_names)
    else:
        dataset = load_dataset(SWE_AGENT_DATASET_ID, split="train")
        print(f"Rows: {len(dataset):,}")
        print(f"Columns: {dataset.column_names}")
        tmp_path = RAW_SWE_AGENT_PATH.with_suffix(".parquet.tmp")
        dataset.to_parquet(str(tmp_path))
        tmp_path.replace(paths.raw_path)
        row_count = len(dataset)
        columns = list(dataset.column_names)

    print(f"Rows: {row_count:,}")
    print(f"Columns: {columns}")

    metadata = _metadata_from_values(row_count, columns, paths.raw_path)
    if args.limit is not None:
        metadata["limited_sample_rows"] = args.limit
    paths.source_metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")

    print(f"Saved data to {paths.raw_path}")
    print(f"Saved source metadata to {paths.source_metadata_path}")


if __name__ == "__main__":
    main()
