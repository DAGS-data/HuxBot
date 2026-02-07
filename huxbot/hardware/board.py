"""Board controller — typed async methods over a HardwareConnection."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from huxbot.hardware.connection import HardwareConnection


class Board:
    """High-level interface to an Arduino/ESP32 board."""

    def __init__(self, connection: HardwareConnection) -> None:
        self._conn = connection
        self._connected = False

    async def connect(self) -> None:
        await self._conn.connect()
        self._connected = True

    async def disconnect(self) -> None:
        await self._conn.disconnect()
        self._connected = False

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("Board not connected — call connect() first")

    async def _cmd(self, command: str) -> str:
        """Send a command and return the parsed result.

        Protocol: ``COMMAND:ARGS`` → ``OK:RESULT`` or ``ERR:MESSAGE``.
        """
        self._ensure_connected()
        raw = await self._conn.send(command)
        if raw.startswith("OK:"):
            return raw[3:]
        if raw.startswith("ERR:"):
            raise RuntimeError(f"Board error: {raw[4:]}")
        raise RuntimeError(f"Unexpected board response: {raw}")

    async def pin_mode(self, pin: int, mode: str) -> str:
        return await self._cmd(f"PIN_MODE:{pin}:{mode.upper()}")

    async def digital_read(self, pin: int) -> int:
        result = await self._cmd(f"DIGITAL_READ:{pin}")
        return int(result)

    async def digital_write(self, pin: int, value: int) -> str:
        return await self._cmd(f"DIGITAL_WRITE:{pin}:{value}")

    async def analog_read(self, pin: int) -> int:
        result = await self._cmd(f"ANALOG_READ:{pin}")
        return int(result)

    async def servo_write(self, pin: int, angle: int) -> str:
        return await self._cmd(f"SERVO_WRITE:{pin}:{angle}")

    async def read_sensor(self, sensor_id: str) -> str:
        return await self._cmd(f"SENSOR_READ:{sensor_id}")

    async def capture_image(self) -> str:
        """Request a camera frame; returns base64-encoded image data."""
        return await self._cmd("CAPTURE_IMAGE")

    async def list_devices(self) -> str:
        return await self._cmd("LIST_DEVICES")
