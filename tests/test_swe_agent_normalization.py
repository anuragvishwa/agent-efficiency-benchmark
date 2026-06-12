from __future__ import annotations

from src.normalization.normalize_swe_agent import (
    build_run_id,
    derive_tool_name,
    extract_action,
    normalize_trajectory,
)


def test_swe_agent_run_id_is_deterministic() -> None:
    row = {
        "instance_id": "repo__issue-1",
        "model_name": "swe-agent-llama-70b",
        "target": True,
        "exit_status": "submitted",
        "generated_patch": "patch",
        "trajectory": [{"role": "ai", "text": "submit"}],
    }
    first, source = build_run_id(row, {})
    second, _ = build_run_id(row, {})
    assert source == "derived"
    assert first == second
    assert first.startswith("sweagent:derived:")


def test_swe_agent_extract_action_and_tool_name() -> None:
    assert extract_action("Run tests\n```pytest -q```") == "pytest -q"
    assert derive_tool_name("pytest -q") == "bash"
    assert derive_tool_name("open src/app.py") == "open"
    assert derive_tool_name("edit src/app.py") == "edit"
    assert derive_tool_name("search error") == "search"
    assert derive_tool_name("submit") == "submit"


def test_swe_agent_pairs_ai_action_with_following_observation() -> None:
    rows, tool_calls = normalize_trajectory(
        run_id="run",
        task_name="task",
        exit_status="submitted",
        trajectory=[
            {"role": "system", "system_prompt": "SETTING", "text": None},
            {"role": "user", "text": "Issue"},
            {"role": "ai", "text": "```pytest -q```"},
            {"role": "user", "text": "AssertionError"},
            {"role": "ai", "text": "```submit```"},
        ],
    )
    assert tool_calls == 2
    assert rows[2]["command"] == "pytest -q"
    assert rows[2]["observation"] == "AssertionError"
    assert rows[3]["tool_name"] == "submit"
