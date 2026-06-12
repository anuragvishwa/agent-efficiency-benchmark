from __future__ import annotations

from pathlib import Path


AFWB_VERSION = "0.1-foundation"
FRAMEWORK = "custom"
MOCK_MODEL_NAME = "mock"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AFWB_DATA_DIR = PROJECT_ROOT / "data" / "afwb"
AFWB_SCENARIOS_DIR = AFWB_DATA_DIR / "scenarios"
AFWB_GOLD_DIR = AFWB_DATA_DIR / "gold"
AFWB_CONFIG_DIR = PROJECT_ROOT / "configs" / "afwb"
AFWB_RESULTS_RAW_DIR = PROJECT_ROOT / "results" / "afwb" / "raw"

REFERENCE_OUTPUT = AFWB_RESULTS_RAW_DIR / "reference_runs.jsonl"
MUTATION_OUTPUT = AFWB_RESULTS_RAW_DIR / "mutated_runs.jsonl"

FOUNDATION_SCENARIO_FILE = AFWB_SCENARIOS_DIR / "foundation.json"
FOUNDATION_GOLD_FILE = AFWB_GOLD_DIR / "foundation.json"

BASE_TIMESTAMP = "2026-06-12T10:00:00.000Z"
