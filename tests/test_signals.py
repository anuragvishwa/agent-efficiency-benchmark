from __future__ import annotations

from src.signals.classifiers import (
    is_edit_action,
    is_test_action,
    normalize_command,
    normalized_action,
    observation_key,
)


def test_command_normalization_removes_unstable_values() -> None:
    command = "python  /tmp/abc/file.py  550e8400-e29b-41d4-a716-446655440000"
    assert normalize_command(command) == "python <TEMP_PATH> <UUID>"


def test_action_classifiers() -> None:
    assert is_test_action("Bash", "pytest -q")
    assert is_edit_action("Edit", None)
    assert normalized_action("Bash", " pytest -q ") == "bash::pytest -q"


def test_observation_key_is_bounded_and_stable() -> None:
    assert observation_key("Error: 123") == observation_key("error: 456")
