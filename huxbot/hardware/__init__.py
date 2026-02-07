"""Hardware control module for Arduino/ESP32 boards."""

from __future__ import annotations

from typing import Any

from huxbot.hardware.board import Board
from huxbot.hardware.connection import (
    HardwareConnection,
    NetworkConnection,
    SerialConnection,
)

__all__ = [
    "Board",
    "HardwareConnection",
    "NetworkConnection",
    "SerialConnection",
    "make_board",
]


def make_board(config: Any) -> Board:
    """Create a Board from a HardwareConfig instance."""
    if config.transport == "network":
        connection: HardwareConnection = NetworkConnection(base_url=config.port)
    else:
        connection = SerialConnection(port=config.port, baudrate=config.baudrate)
    return Board(connection)
