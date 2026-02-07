"""Skill loader – reads markdown files with YAML frontmatter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Skill:
    """A loaded skill definition."""

    name: str
    description: str = ""
    trigger: str = ""
    body: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class SkillsLoader:
    """Load skills from one or more directories of markdown files."""

    def __init__(self, dirs: list[Path]) -> None:
        self.dirs = dirs

    def load_all(self) -> list[Skill]:
        skills: list[Skill] = []
        for d in self.dirs:
            if not d.is_dir():
                continue
            for skill_dir in sorted(d.iterdir()):
                skill_file = skill_dir / "SKILL.md" if skill_dir.is_dir() else None
                if skill_file and skill_file.is_file():
                    skill = self._parse(skill_file, skill_dir.name)
                    if skill:
                        skills.append(skill)
        return skills

    def _parse(self, path: Path, fallback_name: str) -> Skill | None:
        try:
            import frontmatter  # python-frontmatter

            post = frontmatter.load(str(path))
            meta = dict(post.metadata) if post.metadata else {}
            return Skill(
                name=meta.get("name", fallback_name),
                description=meta.get("description", ""),
                trigger=meta.get("trigger", ""),
                body=post.content,
                metadata=meta,
            )
        except Exception:
            # Fallback: plain read without frontmatter
            text = path.read_text(errors="replace")
            return Skill(name=fallback_name, body=text)

    def as_prompt_section(self) -> str:
        """Return a combined prompt section describing all loaded skills."""
        skills = self.load_all()
        if not skills:
            return ""
        parts = ["## Available Skills\n"]
        for s in skills:
            parts.append(f"### {s.name}")
            if s.description:
                parts.append(s.description)
            if s.trigger:
                parts.append(f"Trigger: `{s.trigger}`")
            parts.append(s.body)
            parts.append("")
        return "\n".join(parts)
