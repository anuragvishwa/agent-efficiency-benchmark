from __future__ import annotations


def test_missing_verification_definition() -> None:
    edit_actions = 1
    test_actions = 0
    assert edit_actions > 0 and test_actions == 0
