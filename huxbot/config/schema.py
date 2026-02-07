"""Pydantic configuration models for HuxBot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """LLM provider credentials."""

    name: str = "anthropic"
    api_key: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Agent-level settings."""

    name: str = "huxbot"
    model: str = "anthropic/claude-sonnet-4-20250514"
    workspace: Path = Path(".")
    system_prompt_file: str = "SOUL.md"
    agents_file: str = "AGENTS.md"
    memory_dir: str = "memory"
    skills_dirs: list[str] = Field(default_factory=lambda: ["skills"])
    max_tokens: int = 8192
    temperature: float = 0.7


class ToolsConfig(BaseModel):
    """Tool-level settings."""

    exec_timeout: int = 30
    web_search_api_key: str = ""
    web_search_engine: str = "google"
    allowed_paths: list[str] = Field(default_factory=list)


class HardwareConfig(BaseModel):
    """Hardware board settings."""

    enabled: bool = False
    transport: str = "serial"  # "serial" or "network"
    port: str = "/dev/ttyUSB0"  # serial port or http://host:port
    baudrate: int = 9600
    extra: dict[str, Any] = Field(default_factory=dict)


class ChannelConfig(BaseModel):
    """Single channel config."""

    enabled: bool = False
    token: str = ""
    allow_from: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class ChannelsConfig(BaseModel):
    """All channel configurations."""

    telegram: ChannelConfig = Field(default_factory=ChannelConfig)
    discord: ChannelConfig = Field(default_factory=ChannelConfig)
    whatsapp: ChannelConfig = Field(default_factory=ChannelConfig)


class HuxBotConfig(BaseModel):
    """Root configuration."""

    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
