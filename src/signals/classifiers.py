from __future__ import annotations

import re

from src.common.hashing import text_sha256
from src.common.text import collapse_whitespace


ERROR_PATTERNS = [
    r"command not found",
    r"no such file or directory",
    r"permission denied",
    r"modulenotfounderror",
    r"module not found",
    r"syntaxerror",
    r"syntax error",
    r"traceback",
    r"fatal:",
    r"timed out",
    r"timeout",
    r"segmentation fault",
    r"assertionerror",
    r"tests? failed",
    r"\berror:",
]

TEST_PATTERNS = [
    r"\bpytest\b",
    r"\bpython\s+-m\s+pytest\b",
    r"\bgo test\b",
    r"\bcargo test\b",
    r"\bnpm test\b",
    r"\bnpm run test\b",
    r"\bpnpm test\b",
    r"\byarn test\b",
    r"\bmvn test\b",
    r"\bgradle test\b",
    r"\bmake test\b",
    r"\brspec\b",
]

EDIT_PATTERNS = [
    r"\bapply_patch\b",
    r"\bsed\s+-i\b",
    r"\bperl\s+-pi\b",
    r"\btee\b",
    r"\bcat\s+.*>",
    r"\becho\s+.*>",
    r"\bwrite\b",
    r"\bedit\b",
]

READ_PATTERNS = [
    r"^\s*cat\b",
    r"^\s*head\b",
    r"^\s*tail\b",
    r"^\s*less\b",
    r"^\s*sed\s+-n\b",
    r"^\s*nl\b",
]

SEARCH_PATTERNS = [
    r"\brg\b",
    r"\bgrep\b",
    r"\bfind\b",
    r"\blocate\b",
]

SUBMISSION_PATTERNS = [
    r"\bsubmit\b",
    r"\bfinal answer\b",
    r"\bfinish\b",
]

TEMP_PATH_PATTERN = re.compile(r"(/tmp|/var/folders|/private/var)/[^\s'\"`]+")
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
HEX_PATTERN = re.compile(r"\b[0-9a-f]{32,}\b", re.IGNORECASE)


def matches_any(text: str | None, patterns: list[str]) -> bool:
    value = text or ""
    return any(re.search(pattern, value, re.IGNORECASE) for pattern in patterns)


def normalize_tool_name(tool_name: str | None) -> str:
    return collapse_whitespace(tool_name).lower()


def normalize_command(command: str | None) -> str:
    value = collapse_whitespace(command)
    value = TEMP_PATH_PATTERN.sub("<TEMP_PATH>", value)
    value = UUID_PATTERN.sub("<UUID>", value)
    value = HEX_PATTERN.sub("<HEX>", value)
    return value


def normalized_action(tool_name: str | None, command: str | None) -> str:
    tool = normalize_tool_name(tool_name)
    command_value = normalize_command(command)
    if tool or command_value:
        return f"{tool}::{command_value}"
    return ""


def observation_key(observation: str | None) -> str:
    value = collapse_whitespace(observation).lower()
    value = TEMP_PATH_PATTERN.sub("<TEMP_PATH>", value)
    value = UUID_PATTERN.sub("<UUID>", value)
    value = HEX_PATTERN.sub("<HEX>", value)
    value = re.sub(r"\b\d+\b", "<N>", value)
    return text_sha256(value[:1000], length=24)


def is_shell_action(tool_name: str | None, command: str | None) -> bool:
    tool = normalize_tool_name(tool_name)
    return bool(command and normalize_command(command)) or tool in {
        "bash",
        "shell",
        "terminal",
        "sh",
    }


def is_edit_action(tool_name: str | None, command: str | None) -> bool:
    tool = normalize_tool_name(tool_name)
    return tool in {"write", "edit", "apply_patch"} or matches_any(
        normalize_command(command), EDIT_PATTERNS
    )


def is_read_action(tool_name: str | None, command: str | None) -> bool:
    tool = normalize_tool_name(tool_name)
    return tool in {"read", "open"} or matches_any(normalize_command(command), READ_PATTERNS)


def is_search_action(tool_name: str | None, command: str | None) -> bool:
    tool = normalize_tool_name(tool_name)
    return tool in {"search", "grep"} or matches_any(
        normalize_command(command), SEARCH_PATTERNS
    )


def is_test_action(tool_name: str | None, command: str | None) -> bool:
    tool = normalize_tool_name(tool_name)
    return "test" in tool or matches_any(normalize_command(command), TEST_PATTERNS)


def is_submission_action(tool_name: str | None, command: str | None) -> bool:
    tool = normalize_tool_name(tool_name)
    return "submit" in tool or matches_any(normalize_command(command), SUBMISSION_PATTERNS)
