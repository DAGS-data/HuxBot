"""Telegram channel – long-polling via python-telegram-bot."""

from __future__ import annotations

import asyncio
import logging
import re

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

from huxbot.bus.events import OutboundMessage
from huxbot.bus.queue import MessageBus
from huxbot.channels.base import BaseChannel
from huxbot.config.schema import ChannelConfig

logger = logging.getLogger(__name__)

# Regex that splits text into fenced code blocks, inline code, and plain prose.
_SEGMENT_RE = re.compile(r"(```[\w]*\n?[\s\S]*?```|`[^`]+`)")


def _markdown_to_telegram_html(text: str) -> str:
    """Convert common markdown to Telegram-safe HTML.

    The algorithm splits the source into three segment types—fenced code
    blocks, inline code spans, and everything else—then converts each
    segment independently.  This avoids placeholder / null-byte tricks.
    """
    if not text:
        return ""

    segments = _SEGMENT_RE.split(text)
    parts: list[str] = []

    for seg in segments:
        if seg.startswith("```"):
            # Fenced code block — strip the backtick fences and language tag.
            inner = re.sub(r"^```[\w]*\n?", "", seg)
            inner = inner.removesuffix("```")
            escaped = _html_escape(inner)
            parts.append(f"<pre><code>{escaped}</code></pre>")

        elif seg.startswith("`") and seg.endswith("`"):
            # Inline code span.
            inner = seg[1:-1]
            parts.append(f"<code>{_html_escape(inner)}</code>")

        else:
            # Prose — apply lightweight markdown conversions.
            parts.append(_convert_prose(seg))

    return "".join(parts)


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _convert_prose(text: str) -> str:
    """Apply simple markdown → HTML rules to a non-code segment."""
    text = _html_escape(text)
    # Strip heading markers.
    text = re.sub(r"^#{1,6}\s+(.+)$", r"\1", text, flags=re.MULTILINE)
    # Links.
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Bold.
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic (word-boundary fenced underscores).
    text = re.sub(r"(?<![a-zA-Z0-9])_([^_]+)_(?![a-zA-Z0-9])", r"<i>\1</i>", text)
    # Bullet lists.
    text = re.sub(r"^[-*]\s+", "• ", text, flags=re.MULTILINE)
    return text


class TelegramChannel(BaseChannel):
    """Telegram channel using long-polling."""

    name = "telegram"

    def __init__(self, config: ChannelConfig, bus: MessageBus) -> None:
        super().__init__(config, bus)
        self._app: Application | None = None

    async def start(self) -> None:
        if not self.config.token:
            logger.error("Telegram bot token not configured")
            return

        self._running = True
        self._app = Application.builder().token(self.config.token).build()

        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message)
        )
        self._app.add_handler(CommandHandler("start", self._on_start))

        await self._app.initialize()
        await self._app.start()

        bot_info = await self._app.bot.get_me()
        logger.info("Telegram bot @%s connected", bot_info.username)

        await self._app.updater.start_polling(
            allowed_updates=["message"], drop_pending_updates=True
        )

        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        self._running = False
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
            self._app = None

    async def send(self, msg: OutboundMessage) -> None:
        if not self._app:
            return
        try:
            chat_id = int(msg.recipient)
            html = _markdown_to_telegram_html(msg.text)
            await self._app.bot.send_message(chat_id=chat_id, text=html, parse_mode="HTML")
        except Exception:
            try:
                await self._app.bot.send_message(chat_id=int(msg.recipient), text=msg.text)
            except Exception as exc:
                logger.error("Error sending Telegram message: %s", exc)

    async def _on_start(self, update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message and update.effective_user:
            await update.message.reply_text(
                f"Hi {update.effective_user.first_name}! I'm HuxBot. Send me a message!"
            )

    async def _on_message(self, update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.effective_user:
            return
        user = update.effective_user
        uid = str(user.id)
        ids: set[str] = {uid}
        if user.username:
            ids.add(user.username)

        content = update.message.text or "[empty]"

        await self._forward_to_bus(
            sender_ids=ids,
            chat_id=str(update.message.chat_id),
            content=content,
            metadata={
                "message_id": update.message.message_id,
                "username": user.username,
                "first_name": user.first_name,
            },
        )
