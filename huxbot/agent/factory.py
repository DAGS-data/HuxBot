"""Agent factory – builds an ADK LlmAgent + Runner from HuxBot config."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from huxbot.agent.instruction import InstructionBuilder
from huxbot.bus.queue import MessageBus
from huxbot.config.schema import HuxBotConfig
from huxbot.tools.filesystem import read_file, write_file, edit_file, list_dir
from huxbot.tools.shell import exec_command
from huxbot.tools.web import web_search, web_fetch
from huxbot.tools.message import make_send_message


def build_agent_and_runner(
    config: HuxBotConfig,
    bus: MessageBus,
) -> tuple[LlmAgent, Runner, InMemorySessionService]:
    """Create and return ``(agent, runner, session_service)``."""
    workspace = Path(config.agent.workspace).expanduser().resolve()

    # Resolve skill directories
    skills_dirs = [workspace / d for d in config.agent.skills_dirs]
    # Also include built-in skills shipped with huxbot
    builtin_skills = Path(__file__).parent.parent / "skills"
    if builtin_skills.is_dir():
        skills_dirs.append(builtin_skills)

    instruction_builder = InstructionBuilder(workspace, skills_dirs)

    # Inject API key into environment for LiteLLM
    if config.provider.api_key:
        env_key_map = {
            "openrouter": "OPENROUTER_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
        }
        env_var = env_key_map.get(config.provider.name)
        if env_var:
            os.environ[env_var] = config.provider.api_key

    # Model
    model = LiteLlm(model=config.agent.model)

    # Tools
    send_message = make_send_message(bus)
    tools: list[Any] = [
        read_file,
        write_file,
        edit_file,
        list_dir,
        exec_command,
        web_search,
        web_fetch,
        send_message,
    ]

    # Hardware tools (optional)
    if config.hardware.enabled:
        from huxbot.hardware import make_board
        from huxbot.tools.hardware import make_hardware_tools

        board = make_board(config.hardware)
        tools.extend(make_hardware_tools(board))

    # Agent
    agent = LlmAgent(
        name=config.agent.name,
        model=model,
        instruction=instruction_builder,
        tools=tools,
    )

    # Session service
    session_service = InMemorySessionService()

    # Runner
    runner = Runner(
        app_name="huxbot",
        agent=agent,
        session_service=session_service,
    )

    return agent, runner, session_service
