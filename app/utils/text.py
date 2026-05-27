from __future__ import annotations

from typing import Any


def repair_human_text(value: str | None) -> str | None:
    """Pass-through — encoding is enforced at the connection level (SET NAMES utf8mb4)."""
    return value


def repair_json_text(value: Any) -> Any:
    """Pass-through — encoding is enforced at the connection level (SET NAMES utf8mb4)."""
    return value
