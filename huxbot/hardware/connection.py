"""Transport abstraction for Arduino/ESP32 hardware communication."""

from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable

import aiohttp


@runtime_checkable
class HardwareConnection(Protocol):
    """Protocol for hardware transport layers."""

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send(self, command: str) -> str: ...


class SerialConnection:
    """USB serial connection using pyserial-asyncio."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600) -> None:
        self.port = port
        self.baudrate = baudrate
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        import serial_asyncio  # type: ignore[import-untyped]

        self._reader, self._writer = await serial_asyncio.open_serial_connection(
            url=self.port, baudrate=self.baudrate
        )

    async def disconnect(self) -> None:
        if self._writer:
            self._writer.close()
            self._reader = None
            self._writer = None

    async def send(self, command: str) -> str:
        if not self._writer or not self._reader:
            raise RuntimeError("Serial connection not open — call connect() first")
        self._writer.write(f"{command}\n".encode())
        await self._writer.drain()
        raw = await self._reader.readline()
        return raw.decode().strip()


class NetworkConnection:
    """HTTP connection for WiFi-enabled boards (ESP32 etc.)."""

    def __init__(self, base_url: str = "http://192.168.1.100") -> None:
        self.base_url = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

    async def connect(self) -> None:
        self._session = aiohttp.ClientSession()

    async def disconnect(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def send(self, command: str) -> str:
        if not self._session:
            raise RuntimeError("Network connection not open — call connect() first")
        async with self._session.post(
            f"{self.base_url}/cmd",
            data=command,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            return (await resp.text()).strip()
