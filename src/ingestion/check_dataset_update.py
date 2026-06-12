from __future__ import annotations

import json
import sys

from huggingface_hub import HfApi

from src.common.constants import DATASET_ID, SOURCE_METADATA_PATH


def main() -> None:
    try:
        if not SOURCE_METADATA_PATH.exists():
            print("NO_LOCAL_REVISION")
            raise SystemExit(3)
        metadata = json.loads(SOURCE_METADATA_PATH.read_text())
        local_revision = metadata.get("revision")
        if not local_revision:
            print("NO_LOCAL_REVISION")
            raise SystemExit(3)
        remote_revision = getattr(HfApi().dataset_info(DATASET_ID), "sha", None)
        if remote_revision == local_revision:
            print("UP_TO_DATE")
            raise SystemExit(0)
        print("UPDATE_AVAILABLE")
        raise SystemExit(2)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
