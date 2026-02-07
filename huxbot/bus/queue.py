"""Unified async message bus with activity signaling and drain support."""

from __future__ import annotations

import asyncio
from typing import Literal

from huxbot.bus.events import InboundMessage, OutboundMessage

Direction = Literal["inbound", "outbound"]


class MessageBus:
    """Async message bus backed by a dict of named queues.

    Provides publish/consume helpers, an activity event for waiters,
    and a drain mechanism for graceful shutdown.
    """

    def __init__(self, *, maxsize: int = 0) -> None:
        self._queues: dict[Direction, asyncio.Queue] = {
            "inbound": asyncio.Queue(maxsize=maxsize),
            "outbound": asyncio.Queue(maxsize=maxsize),
        }
        self._activity = asyncio.Event()
        self._totals: dict[Direction, int] = {"inbound": 0, "outbound": 0}

    # -- inbound helpers (expected by consumers) --

    async def publish_inbound(self, msg: InboundMessage) -> None:
        await self._queues["inbound"].put(msg)
        self._totals["inbound"] += 1
        self._activity.set()

    async def consume_inbound(self) -> InboundMessage:
        return await self._queues["inbound"].get()

    # -- outbound helpers (expected by consumers) --

    async def publish_outbound(self, msg: OutboundMessage) -> None:
        await self._queues["outbound"].put(msg)
        self._totals["outbound"] += 1
        self._activity.set()

    async def consume_outbound(self) -> OutboundMessage:
        return await self._queues["outbound"].get()

    # -- size properties (expected by consumers) --

    @property
    def inbound_size(self) -> int:
        return self._queues["inbound"].qsize()

    @property
    def outbound_size(self) -> int:
        return self._queues["outbound"].qsize()

    # -- extended API --

    def total_messages(self, direction: Direction) -> int:
        """Return the cumulative number of messages published in *direction*."""
        return self._totals[direction]

    async def wait_for_activity(self, timeout: float | None = None) -> bool:
        """Block until a message is published. Returns False on timeout."""
        try:
            await asyncio.wait_for(self._activity.wait(), timeout)
            self._activity.clear()
            return True
        except asyncio.TimeoutError:
            return False

    async def drain(self) -> int:
        """Discard all pending messages and return total drained count."""
        count = 0
        for q in self._queues.values():
            while not q.empty():
                try:
                    q.get_nowait()
                    count += 1
                except asyncio.QueueEmpty:
                    break
        return count
