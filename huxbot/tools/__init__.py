"""HuxBot tools – plain async functions that ADK auto-wraps as FunctionTool."""

from huxbot.tools.filesystem import read_file, write_file, edit_file, list_dir
from huxbot.tools.shell import exec_command
from huxbot.tools.web import web_search, web_fetch
from huxbot.tools.message import make_send_message
from huxbot.tools.hardware import make_hardware_tools

__all__ = [
    "read_file",
    "write_file",
    "edit_file",
    "list_dir",
    "exec_command",
    "web_search",
    "web_fetch",
    "make_send_message",
    "make_hardware_tools",
]
