"""Hardware tools — ADK-compatible async functions for board control."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from huxbot.hardware.board import Board


def make_hardware_tools(board: "Board") -> list:
    """Return hardware tool functions closed over a Board instance."""

    async def hardware_pin_mode(pin: int, mode: str) -> str:
        """Set a GPIO pin mode. *mode* should be INPUT, OUTPUT, or INPUT_PULLUP."""
        result = await board.pin_mode(pin, mode)
        return f"Pin {pin} set to {mode.upper()} — {result}"

    async def hardware_digital_read(pin: int) -> str:
        """Read the digital value (0 or 1) from a GPIO pin."""
        value = await board.digital_read(pin)
        return f"Pin {pin} digital value: {value}"

    async def hardware_digital_write(pin: int, value: int) -> str:
        """Write a digital value (0 or 1) to a GPIO pin."""
        result = await board.digital_write(pin, value)
        return f"Pin {pin} set to {value} — {result}"

    async def hardware_analog_read(pin: int) -> str:
        """Read the analog value (0-1023) from an analog pin."""
        value = await board.analog_read(pin)
        return f"Pin {pin} analog value: {value}"

    async def hardware_servo_write(pin: int, angle: int) -> str:
        """Move a servo on *pin* to *angle* degrees (0-180)."""
        result = await board.servo_write(pin, angle)
        return f"Servo on pin {pin} moved to {angle}° — {result}"

    async def hardware_read_sensor(sensor_id: str) -> str:
        """Read a value from the sensor identified by *sensor_id*."""
        value = await board.read_sensor(sensor_id)
        return f"Sensor {sensor_id}: {value}"

    async def hardware_capture_image(save_path: str = "capture.jpg") -> str:
        """Capture an image from the board camera and save it to *save_path*."""
        b64_data = await board.capture_image()
        out = Path(save_path)
        out.write_bytes(base64.b64decode(b64_data))
        return f"Image saved to {out.resolve()}"

    return [
        hardware_pin_mode,
        hardware_digital_read,
        hardware_digital_write,
        hardware_analog_read,
        hardware_servo_write,
        hardware_read_sensor,
        hardware_capture_image,
    ]
