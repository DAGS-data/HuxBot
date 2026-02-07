"""Message tool – sends outbound messages via the bus."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from huxbot.bus.queue import MessageBus


def make_send_message(bus: "MessageBus"):
    """Return an async *send_message* function closed over *bus*.

    This lets ADK auto-wrap it as a FunctionTool while keeping a
    reference to the shared message bus.
    """

    async def send_message(channel: str, recipient: str, text: str) -> str:
        """Send a message to *recipient* on *channel* (e.g. 'telegram', 'discord')."""
        from huxbot.bus.events import OutboundMessage

        msg = OutboundMessage(channel=channel, recipient=recipient, text=text)
        await bus.publish_outbound(msg)
        return f"Message queued for {recipient} on {channel}."

    return send_message
