"""Pydantic-based event models for the HuxBot message bus."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field


class InboundMessage(BaseModel):
    """A message arriving from a chat platform into the bus."""

    channel: str
    sender_id: str
    chat_id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    media: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def session_key(self) -> str:
        return f"{self.channel}:{self.chat_id}"

    def __str__(self) -> str:
        preview = self.content[:60] + ("..." if len(self.content) > 60 else "")
        return f"[{self.channel}] {self.sender_id}: {preview}"


class OutboundMessage(BaseModel):
    """A message leaving the bus toward a chat platform."""

    channel: str
    recipient: str
    text: str
    reply_to: str | None = None
    media: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    def __str__(self) -> str:
        preview = self.text[:60] + ("..." if len(self.text) > 60 else "")
        return f"[{self.channel}] -> {self.recipient}: {preview}"
