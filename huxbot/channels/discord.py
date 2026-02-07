"""Discord channel – WebSocket gateway + REST API."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from huxbot.bus.events import OutboundMessage
from huxbot.bus.queue import MessageBus
from huxbot.channels.base import BaseChannel
from huxbot.config.schema import ChannelConfig

logger = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"


class DiscordChannel(BaseChannel):
    """Discord channel using the Gateway WebSocket."""

    name = "discord"

    def __init__(self, config: ChannelConfig, bus: MessageBus) -> None:
        super().__init__(config, bus)
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None
        self._seq: int | None = None
        self._heartbeat_task: asyncio.Task | None = None

    async def start(self) -> None:
        if not self.config.token:
            logger.error("Discord bot token not configured")
            return

        self._running = True
        self._session = aiohttp.ClientSession()

        while self._running:
            try:
                logger.info("Connecting to Discord gateway...")
                self._ws = await self._session.ws_connect(GATEWAY_URL)
                await self._gateway_loop()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("Discord gateway error: %s", exc)
                if self._running:
                    await asyncio.sleep(5)

    async def stop(self) -> None:
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()

    async def send(self, msg: OutboundMessage) -> None:
        if not self._session:
            return
        url = f"{DISCORD_API}/channels/{msg.recipient}/messages"
        headers = {"Authorization": f"Bot {self.config.token}"}
        payload: dict[str, Any] = {"content": msg.text}
        try:
            async with self._session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 429:
                    data = await resp.json()
                    await asyncio.sleep(float(data.get("retry_after", 1.0)))
                    async with self._session.post(url, headers=headers, json=payload) as retry:
                        retry.raise_for_status()
                else:
                    resp.raise_for_status()
        except Exception as exc:
            logger.error("Error sending Discord message: %s", exc)

    async def _gateway_loop(self) -> None:
        if not self._ws:
            return
        async for raw_msg in self._ws:
            if raw_msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                break
            try:
                data = json.loads(raw_msg.data)
            except (json.JSONDecodeError, TypeError):
                continue

            op = data.get("op")
            payload = data.get("d")
            seq = data.get("s")
            event_type = data.get("t")

            if seq is not None:
                self._seq = seq

            if op == 10:
                interval = payload.get("heartbeat_interval", 45000) / 1000
                await self._start_heartbeat(interval)
                await self._identify()
            elif op == 0 and event_type == "READY":
                logger.info("Discord gateway READY")
            elif op == 0 and event_type == "MESSAGE_CREATE":
                await self._on_message(payload)
            elif op in (7, 9):
                break

    async def _identify(self) -> None:
        if not self._ws:
            return
        await self._ws.send_json({
            "op": 2,
            "d": {
                "token": self.config.token,
                "intents": self.config.extra.get("intents", 513),
                "properties": {"os": "huxbot", "browser": "huxbot", "device": "huxbot"},
            },
        })

    async def _start_heartbeat(self, interval: float) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        async def _loop() -> None:
            while self._running and self._ws:
                await self._ws.send_json({"op": 1, "d": self._seq})
                await asyncio.sleep(interval)

        self._heartbeat_task = asyncio.create_task(_loop())

    async def _on_message(self, payload: dict[str, Any]) -> None:
        author = payload.get("author") or {}
        if author.get("bot"):
            return
        sender_id = str(author.get("id", ""))
        channel_id = str(payload.get("channel_id", ""))
        content = payload.get("content") or "[empty]"
        if not sender_id or not channel_id:
            return
        await self._forward_to_bus(
            sender_ids={sender_id},
            chat_id=channel_id,
            content=content,
            metadata={"message_id": str(payload.get("id", ""))},
        )
