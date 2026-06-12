from __future__ import annotations

import re


ALIASES = {
    "claude-opus-4.6@anthropic": "claude-opus-4-6@anthropic",
    "claude-opus-4.7@anthropic": "claude-opus-4-7@anthropic",
    "gpt-5.3-codex@openai": "gpt-5.3-codex@openai",
}


def canonicalize_model_name(value: str | None) -> str | None:
    if value is None:
        return None
    name = value.strip().lower()
    if not name:
        return None
    name = re.sub(r"\s+", "", name)
    name = name.replace("claude-opus-4.6", "claude-opus-4-6")
    name = name.replace("claude-opus-4.7", "claude-opus-4-7")
    name = name.replace("gpt_5", "gpt-5")
    name = re.sub(r"@openai$", "@openai", name)
    name = re.sub(r"@google$", "@google", name)
    name = re.sub(r"@anthropic$", "@anthropic", name)
    return ALIASES.get(name, name)
