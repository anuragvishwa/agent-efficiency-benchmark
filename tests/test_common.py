from __future__ import annotations

from src.common.model_names import canonicalize_model_name
from src.common.numeric import to_float, to_int
from src.common.text import to_text


def test_text_conversion_is_deterministic_json() -> None:
    assert to_text({"b": 1, "a": 2}) == '{"a": 2, "b": 1}'
    assert to_text(True) == "True"


def test_numeric_rejects_non_finite() -> None:
    assert to_float("") is None
    assert to_float("nan") is None
    assert to_float("inf") is None
    assert to_int("3.0") == 3


def test_model_aliases_are_conservative() -> None:
    assert canonicalize_model_name("Claude-Opus-4.6@Anthropic") == (
        "claude-opus-4-6@anthropic"
    )
    assert canonicalize_model_name("gpt-5.5@openai") == "gpt-5.5@openai"
