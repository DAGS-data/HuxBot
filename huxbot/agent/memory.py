"""Memory store – reads MEMORY.md and daily notes from the workspace."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from huxbot.utils.helpers import ensure_dir


class MemoryStore:
    """Read/write the agent's long-term memory (markdown files)."""

    def __init__(self, workspace: Path) -> None:
        self.memory_dir = ensure_dir(workspace / "memory")
        self.memory_file = self.memory_dir / "MEMORY.md"

    def read(self) -> str:
        """Return the contents of MEMORY.md (empty string if missing)."""
        if self.memory_file.is_file():
            return self.memory_file.read_text(errors="replace")
        return ""

    def read_daily(self) -> str:
        """Return today's daily-note, if it exists."""
        today = date.today().isoformat()
        daily = self.memory_dir / f"{today}.md"
        if daily.is_file():
            return daily.read_text(errors="replace")
        return ""

    def append(self, text: str) -> None:
        """Append *text* to MEMORY.md."""
        with self.memory_file.open("a") as f:
            f.write("\n" + text)

    def append_daily(self, text: str) -> None:
        """Append *text* to today's daily-note."""
        today = date.today().isoformat()
        daily = self.memory_dir / f"{today}.md"
        with daily.open("a") as f:
            f.write("\n" + text)
