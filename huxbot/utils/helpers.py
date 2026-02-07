"""Utility helpers for HuxBot."""

from __future__ import annotations

import re
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Create directory (and parents) if it doesn't exist, return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    """Convert an arbitrary string into a filesystem-safe filename."""
    return re.sub(r"[^\w\-.]", "_", name).strip("_")[:255]


def truncate(text: str, max_len: int = 4000) -> str:
    """Truncate text to *max_len* characters, appending '…' if trimmed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
