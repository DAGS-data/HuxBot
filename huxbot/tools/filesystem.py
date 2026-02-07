"""Filesystem tools for HuxBot."""

from __future__ import annotations

import os
from pathlib import Path


async def read_file(path: str) -> str:
    """Read and return the contents of a file at *path*."""
    p = Path(path).expanduser()
    if not p.is_file():
        return f"Error: {path} is not a file or does not exist."
    try:
        return p.read_text(errors="replace")
    except Exception as exc:
        return f"Error reading {path}: {exc}"


async def write_file(path: str, content: str) -> str:
    """Write *content* to a file at *path*, creating parent directories as needed."""
    p = Path(path).expanduser()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Wrote {len(content)} characters to {path}."
    except Exception as exc:
        return f"Error writing {path}: {exc}"


async def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Replace the first occurrence of *old_string* with *new_string* in a file."""
    p = Path(path).expanduser()
    if not p.is_file():
        return f"Error: {path} does not exist."
    try:
        text = p.read_text()
        if old_string not in text:
            return f"Error: old_string not found in {path}."
        p.write_text(text.replace(old_string, new_string, 1))
        return f"Edited {path} successfully."
    except Exception as exc:
        return f"Error editing {path}: {exc}"


async def list_dir(path: str = ".") -> str:
    """List directory contents at *path*."""
    p = Path(path).expanduser()
    if not p.is_dir():
        return f"Error: {path} is not a directory."
    try:
        entries = sorted(p.iterdir())
        lines: list[str] = []
        for e in entries:
            suffix = "/" if e.is_dir() else ""
            size = e.stat().st_size if e.is_file() else 0
            lines.append(f"{'d' if e.is_dir() else 'f'}  {size:>8}  {e.name}{suffix}")
        return "\n".join(lines) if lines else "(empty directory)"
    except Exception as exc:
        return f"Error listing {path}: {exc}"
