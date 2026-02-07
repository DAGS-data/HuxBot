"""Load and save HuxBot configuration from ~/.huxbot/config.json."""

from __future__ import annotations

import json
from pathlib import Path

from huxbot.config.schema import HuxBotConfig
from huxbot.utils.helpers import ensure_dir

CONFIG_DIR = Path.home() / ".huxbot"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config(path: Path | None = None) -> HuxBotConfig:
    """Load config from *path* (default ~/.huxbot/config.json)."""
    p = path or CONFIG_FILE
    if p.exists():
        data = json.loads(p.read_text())
        return HuxBotConfig.model_validate(data)
    return HuxBotConfig()


def save_config(config: HuxBotConfig, path: Path | None = None) -> Path:
    """Persist config to disk and return the file path."""
    p = path or CONFIG_FILE
    ensure_dir(p.parent)
    p.write_text(config.model_dump_json(indent=2) + "\n")
    return p
