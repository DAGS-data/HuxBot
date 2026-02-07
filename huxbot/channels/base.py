"""Base channel interface for chat platforms."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from huxbot.bus.events import InboundMessage, OutboundMessage
from huxbot.bus.queue import MessageBus
from huxbot.config.schema import ChannelConfig

logger = logging.getLogger(__name__)


class BaseChannel(ABC):
    """Abstract base class for chat channel implementations."""

    name: str = "base"

    def __init__(self, config: ChannelConfig, bus: MessageBus) -> None:
        self.config = config
        self.bus = bus
        self._running = False

    @abstractmethod
    async def start(self) -> None:
        """Start the channel (long-running coroutine)."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel and clean up."""

    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """Send an outbound message through this channel."""

    def _check_access(self, sender_ids: set[str]) -> bool:
        """Return True if any of *sender_ids* is in the allow list.

        When no allow list is configured every sender is permitted.
        Callers are responsible for splitting composite identifiers
        (e.g. ``"12345|username"``) *before* calling this method.
        """
        allow_list = self.config.allow_from
        if not allow_list:
            return True
        return bool(sender_ids & set(allow_list))

    async def _forward_to_bus(
        self,
        *,
        sender_ids: set[str],
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Validate access and publish an inbound message to the bus.

        *sender_ids* is the full set of identifiers for the sender
        (numeric id, username, etc.).  The first element is used as the
        canonical ``sender_id`` on the event.
        """
        if not self._check_access(sender_ids):
            logger.warning("Access denied for %s on %s", sender_ids, self.name)
            return

        msg = InboundMessage(
            channel=self.name,
            sender_id=next(iter(sender_ids)),
            chat_id=str(chat_id),
            content=content,
            media=media or [],
            metadata=metadata or {},
        )
        await self.bus.publish_inbound(msg)

    @property
    def is_running(self) -> bool:
        return self._running
