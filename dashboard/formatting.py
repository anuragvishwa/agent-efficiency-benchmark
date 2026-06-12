from __future__ import annotations


def pct(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.1%}"


def money(value: float | int | None) -> str:
    if value is None:
        return "Cost data insufficient"
    return f"${float(value):,.2f}"
