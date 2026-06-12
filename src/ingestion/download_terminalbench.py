from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset
from huggingface_hub import HfApi

from src.common.constants import DATASET_ID, RAW_TERMINALBENCH_PATH, SOURCE_METADATA_PATH


def _metadata(dataset, output_path: Path) -> dict[str, object]:
    info = HfApi().dataset_info(DATASET_ID)
    return {
        "dataset_id": DATASET_ID,
        "revision": getattr(info, "sha", None),
        "last_modified": (
            info.last_modified.isoformat() if getattr(info, "last_modified", None) else None
        ),
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "split": "train",
        "row_count": len(dataset),
        "columns": list(dataset.column_names),
        "local_file": str(output_path),
        "local_file_size": output_path.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    RAW_TERMINALBENCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    if RAW_TERMINALBENCH_PATH.exists() and not args.force:
        raise SystemExit(
            f"{RAW_TERMINALBENCH_PATH} already exists. Re-run with --force to overwrite."
        )

    dataset = load_dataset(
        DATASET_ID,
        split="train",
    )

    print(f"Rows: {len(dataset):,}")
    print(f"Columns: {dataset.column_names}")

    tmp_path = RAW_TERMINALBENCH_PATH.with_suffix(".parquet.tmp")
    dataset.to_parquet(str(tmp_path))
    tmp_path.replace(RAW_TERMINALBENCH_PATH)

    metadata = _metadata(dataset, RAW_TERMINALBENCH_PATH)
    SOURCE_METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n")

    print(f"Saved data to {RAW_TERMINALBENCH_PATH}")
    print(f"Saved source metadata to {SOURCE_METADATA_PATH}")


if __name__ == "__main__":
    main()
