"""Message processor – bridges the message bus with the ADK Runner."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from huxbot.bus.events import InboundMessage, OutboundMessage
from huxbot.bus.queue import MessageBus

logger = logging.getLogger(__name__)

APP_NAME = "huxbot"
DEFAULT_USER = "default_user"


class MessageProcessor:
    """Consume inbound messages, run the ADK agent, and publish responses."""

    def __init__(
        self,
        runner: Runner,
        session_service: InMemorySessionService,
        bus: MessageBus,
    ) -> None:
        self.runner = runner
        self.session_service = session_service
        self.bus = bus
        self._running = False

    async def run(self) -> None:
        """Main loop – consume from bus, invoke runner, publish reply."""
        self._running = True
        logger.info("MessageProcessor started")

        while self._running:
            try:
                msg = await asyncio.wait_for(self.bus.consume_inbound(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            try:
                reply = await self._process(msg)
                if reply:
                    out = OutboundMessage(
                        channel=msg.channel,
                        recipient=msg.chat_id,
                        text=reply,
                    )
                    await self.bus.publish_outbound(out)
            except Exception:
                logger.exception("Error processing message from %s", msg.session_key)

    async def _process(self, msg: InboundMessage) -> str | None:
        """Run the ADK agent for a single inbound message."""
        user_id = msg.sender_id or DEFAULT_USER
        session_id = msg.session_key

        # Get or create session
        session = await self.session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        if session is None:
            session = await self.session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )

        # Build user content
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=msg.content)],
        )

        # Collect all text parts from the agent's response events
        parts: list[str] = []
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        parts.append(part.text)

        return "".join(parts) if parts else None

    async def process_single(self, text: str, session_id: str = "cli:default") -> str | None:
        """Process a single text message (for CLI / direct use)."""
        msg = InboundMessage(
            channel="cli",
            sender_id="cli_user",
            chat_id=session_id,
            content=text,
        )
        return await self._process(msg)

    def stop(self) -> None:
        self._running = False
