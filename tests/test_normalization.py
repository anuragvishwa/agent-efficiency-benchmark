from __future__ import annotations

from src.normalization.normalize_terminalbench import build_run_id, parse_steps


def test_parse_steps_requires_list() -> None:
    assert parse_steps("null") == []
    assert parse_steps('{"not":"a list"}') == []
    assert parse_steps('[{"src":"assistant"}]') == [{"src": "assistant"}]


def test_build_run_id_uses_trial_id_and_marks_duplicates() -> None:
    seen: dict[str, int] = {}
    row = {"trial_id": "abc"}
    assert build_run_id(row, seen) == ("terminalbench:trial:abc", "trial_id")
    assert build_run_id(row, seen) == (
        "terminalbench:trial:abc:duplicate-2",
        "trial_id_duplicate",
    )


def test_build_run_id_derives_stable_missing_ids() -> None:
    row = {
        "trial_id": "",
        "trial_name": "trial",
        "task_name": "task",
        "agent": "agent",
        "model": "model",
        "started_at": "2026-01-01T00:00:00Z",
        "ended_at": "2026-01-01T00:01:00Z",
        "reward": 0,
        "steps": "[]",
    }
    first, source = build_run_id(row, {})
    second, _ = build_run_id(row, {})
    assert source == "derived"
    assert first == second
    assert first.startswith("terminalbench:derived:")
