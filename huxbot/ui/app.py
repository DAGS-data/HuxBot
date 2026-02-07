"""Streamlit chat UI for HuxBot."""

from __future__ import annotations

import asyncio

import streamlit as st

from huxbot.config import load_config
from huxbot.bus.queue import MessageBus
from huxbot.agent.factory import build_agent_and_runner
from huxbot.agent.processor import MessageProcessor

st.set_page_config(page_title="HuxBot", page_icon="🤖")
st.title("HuxBot")


@st.cache_resource
def _build_processor() -> MessageProcessor:
    config = load_config()
    if not config.provider.api_key:
        st.error("No API key configured. Set it in ~/.huxbot/config.json → provider.api_key")
        st.stop()
    bus = MessageBus()
    _agent, runner, session_service = build_agent_and_runner(config, bus)
    return MessageProcessor(runner, session_service, bus)


processor = _build_processor()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new input
if prompt := st.chat_input("Type a message…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            response = asyncio.run(
                processor.process_single(prompt, session_id="streamlit:default")
            )
        content = response or "(no response)"
        st.markdown(content)

    st.session_state.messages.append({"role": "assistant", "content": content})
