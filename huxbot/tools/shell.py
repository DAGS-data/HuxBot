"""Shell execution tool for HuxBot."""

from __future__ import annotations

import asyncio

from huxbot.utils.helpers import truncate

DEFAULT_TIMEOUT = 30


async def exec_command(command: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Execute a shell command and return its combined stdout/stderr.

    *timeout* is in seconds.
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode(errors="replace")
        err = stderr.decode(errors="replace")
        result = ""
        if out:
            result += out
        if err:
            result += f"\n[stderr]\n{err}"
        result += f"\n[exit code: {proc.returncode}]"
        return truncate(result)
    except asyncio.TimeoutError:
        proc.kill()  # type: ignore[union-attr]
        return f"Error: command timed out after {timeout}s."
    except Exception as exc:
        return f"Error executing command: {exc}"
