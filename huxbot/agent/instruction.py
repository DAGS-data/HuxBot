"""Instruction builder – assembles the system prompt for ADK's LlmAgent."""

from __future__ import annotations

from pathlib import Path

from huxbot.agent.memory import MemoryStore
from huxbot.agent.skills import SkillsLoader


class InstructionBuilder:
    """Build the system-prompt string from workspace files, memory, and skills.

    Returns a *callable* suitable for ADK's ``LlmAgent(instruction=...)``.
    """

    def __init__(self, workspace: Path, skills_dirs: list[Path] | None = None) -> None:
        self.workspace = workspace
        self.memory = MemoryStore(workspace)
        self.skills_loader = SkillsLoader(skills_dirs or [])

    def _read_file(self, name: str) -> str:
        p = self.workspace / name
        if p.is_file():
            return p.read_text(errors="replace")
        return ""

    def build(self) -> str:
        """Assemble the full system prompt."""
        parts: list[str] = []

        # SOUL.md – personality & core behaviour
        soul = self._read_file("SOUL.md")
        if soul:
            parts.append(soul)

        # AGENTS.md – agent instructions
        agents = self._read_file("AGENTS.md")
        if agents:
            parts.append(agents)

        # Long-term memory
        mem = self.memory.read()
        if mem:
            parts.append("## Memory\n" + mem)

        daily = self.memory.read_daily()
        if daily:
            parts.append("## Today's Notes\n" + daily)

        # Skills
        skills_section = self.skills_loader.as_prompt_section()
        if skills_section:
            parts.append(skills_section)

        return "\n\n".join(parts)

    def __call__(self, _ctx=None) -> str:
        """ADK InstructionProvider interface (sync callable)."""
        return self.build()
