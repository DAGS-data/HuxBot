"""WhatsApp channel – connects to a Node.js bridge via WebSocket."""

from __future__ import annotations

import asyncio
import json
import logging

import aiohttp

from huxbot.bus.events import OutboundMessage
from huxbot.bus.queue import MessageBus
from huxbot.channels.base import BaseChannel
from huxbot.config.schema import ChannelConfig

logger = logging.getLogger(__name__)


class WhatsAppChannel(BaseChannel):
    """WhatsApp channel via a Node.js bridge (baileys)."""

    name = "whatsapp"

    def __init__(self, config: ChannelConfig, bus: MessageBus) -> None:
        super().__init__(config, bus)
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        bridge_url = self.config.extra.get("bridge_url", "ws://localhost:3001")

        self._running = True
        self._session = aiohttp.ClientSession()

        while self._running:
            try:
                logger.info("Connecting to WhatsApp bridge at %s...", bridge_url)
                self._ws = await self._session.ws_connect(bridge_url)
                logger.info("Connected to WhatsApp bridge")
                async for raw_msg in self._ws:
                    if raw_msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
                    try:
                        await self._handle_bridge_message(raw_msg.data)
                    except Exception as exc:
                        logger.error("Error handling bridge message: %s", exc)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("WhatsApp bridge error: %s", exc)
                if self._running:
                    await asyncio.sleep(5)

    async def stop(self) -> None:
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()

    async def send(self, msg: OutboundMessage) -> None:
        if not self._ws:
            return
        try:
            await self._ws.send_json({"type": "send", "to": msg.recipient, "text": msg.text})
        except Exception as exc:
            logger.error("Error sending WhatsApp message: %s", exc)

    async def _handle_bridge_message(self, raw: str) -> None:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return

        if data.get("type") == "message":
            sender = data.get("sender", "")
            content = data.get("content", "")
            chat_id = sender.split("@")[0] if "@" in sender else sender
            await self._forward_to_bus(
                sender_ids={chat_id},
                chat_id=sender,
                content=content,
                metadata={"message_id": data.get("id"), "is_group": data.get("isGroup", False)},
            )
        elif data.get("type") == "status":
            logger.info("WhatsApp status: %s", data.get("status"))
