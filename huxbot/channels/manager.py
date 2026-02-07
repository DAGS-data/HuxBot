"""Channel lifecycle and outbound routing for HuxBot."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from huxbot.bus.queue import MessageBus
from huxbot.channels.base import BaseChannel
from huxbot.config.schema import ChannelConfig, HuxBotConfig

logger = logging.getLogger(__name__)

# Registry mapping channel name → (config attr name, module path, class name).
# Adding a new channel only requires a new entry here.
_CHANNEL_REGISTRY: list[tuple[str, str, str]] = [
    ("telegram", "huxbot.channels.telegram", "TelegramChannel"),
    ("discord", "huxbot.channels.discord", "DiscordChannel"),
    ("whatsapp", "huxbot.channels.whatsapp", "WhatsAppChannel"),
]


def _load_channel(
    name: str, module: str, cls_name: str, cfg: ChannelConfig, bus: MessageBus
) -> BaseChannel | None:
    """Try to import and instantiate a single channel.  Returns *None* on failure."""
    try:
        import importlib

        mod = importlib.import_module(module)
        cls = getattr(mod, cls_name)
        return cls(cfg, bus)
    except (ImportError, AttributeError) as exc:
        logger.warning("Could not load %s channel: %s", name, exc)
        return None


class ChannelManager:
    """Owns channel lifecycles and fans outbound messages to the right channel."""

    def __init__(self, config: HuxBotConfig, bus: MessageBus) -> None:
        self.bus = bus
        self._channels: dict[str, BaseChannel] = {}
        self._tasks: list[asyncio.Task] = []

        for name, module, cls_name in _CHANNEL_REGISTRY:
            cfg: ChannelConfig = getattr(config.channels, name)
            if not cfg.enabled:
                continue
            ch = _load_channel(name, module, cls_name, cfg, bus)
            if ch is not None:
                self._channels[name] = ch
                logger.info("Registered %s channel", name)

    # -- public API used by CLI --------------------------------------------------

    @property
    def enabled_channels(self) -> list[str]:
        return list(self._channels)

    async def start_all(self) -> None:
        """Launch every registered channel and the outbound router."""
        if not self._channels:
            logger.warning("No channels registered — nothing to start")
            return

        self._tasks = [
            asyncio.create_task(self._route_outbound(), name="outbound-router"),
            *(
                asyncio.create_task(ch.start(), name=f"channel-{name}")
                for name, ch in self._channels.items()
            ),
        ]
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop_all(self) -> None:
        """Cancel running tasks, then gracefully stop each channel."""
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        for name, ch in self._channels.items():
            try:
                await ch.stop()
            except Exception as exc:
                logger.error("Error stopping %s: %s", name, exc)

    def get_status(self) -> dict[str, Any]:
        return {
            name: {"running": ch.is_running} for name, ch in self._channels.items()
        }

    # -- internals ---------------------------------------------------------------

    async def _route_outbound(self) -> None:
        """Wait for outbound messages and deliver them to the matching channel."""
        while True:
            if not await self.bus.wait_for_activity(timeout=2.0):
                continue
            while self.bus.outbound_size:
                msg = await self.bus.consume_outbound()
                ch = self._channels.get(msg.channel)
                if ch is None:
                    logger.warning("No channel registered for %r", msg.channel)
                    continue
                try:
                    await ch.send(msg)
                except Exception as exc:
                    logger.error("Failed to deliver to %s: %s", msg.channel, exc)
