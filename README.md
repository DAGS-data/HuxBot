<h1 align="center">Huxbot, your personal assistant that can control your Arduino hardware</h1>

<p align="center">
  <img src="./colibre.png" alt="HuxBot" width="200">
</p>

<p align="center">
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <a href="https://github.com/google/adk-python"><img src="https://img.shields.io/badge/Google-ADK-4285F4?style=flat&logo=google&logoColor=white" alt="Google ADK"></a>
    <a href="https://github.com/BerriAI/litellm"><img src="https://img.shields.io/badge/LiteLLM-Powered-orange?style=flat" alt="LiteLLM"></a>
    <img src="https://img.shields.io/badge/Arduino-Compatible-00979D?style=flat&logo=arduino&logoColor=white" alt="Arduino">
</p>

A lightweight personal AI assistant designed to run on edge devices like the **Arduino UNO Q**, **Raspberry Pi**, and **Orange Pi**. You don't need a Mac Mini — just a small board with 2 GB of RAM running Debian Linux is enough. Talk to it on **Telegram**, **Discord**, or **WhatsApp** — it can read and write files, run shell commands, search the web, control hardware, and remember things across conversations.

Built on [Google ADK](https://github.com/google/adk-python) and [LiteLLM](https://github.com/BerriAI/litellm), so it works with any LLM provider (Anthropic, OpenAI, Google, Groq, and more).

Inspired by [OpenClaw](https://github.com/pydantic/openclaw), [Nanobot](https://github.com/nano-bot/nanobot), and named after [Huitzilopochtli](https://en.wikipedia.org/wiki/Huitzilopochtli) — the Aztec god of sun and war.

## How It Works

```
[Telegram / Discord / WhatsApp] → MessageBus → MessageProcessor → ADK Runner → MessageBus → Channels
```

- **Chat channels** receive your messages and forward them to the assistant
- **The assistant** processes your request, uses tools if needed, and sends a reply back
- **Memory & skills** let you customize its personality and teach it new abilities
- **Multi-provider support** lets you use whichever LLM you prefer

## Installation

**Requirements:** Python 3.11+

> **Edge-device friendly:** HuxBot runs on boards like the Arduino UNO Q, Raspberry Pi, and Orange Pi. No Mac Mini required — a 2 GB board with Debian Linux is all you need. The lightweight dependency footprint keeps memory free for the agent and hardware control.

```bash
git clone https://github.com/yourusername/huxbot.git
cd huxbot
pip install -e .
```

## Quick Start

### 1. Initialize

```bash
huxbot onboard
```

This creates:
- `~/.huxbot/config.json` – configuration file
- Workspace files (`AGENTS.md`, `SOUL.md`, `memory/MEMORY.md`)

### 2. Configure your API key

Edit `~/.huxbot/config.json`:

```json
{
  "provider": {
    "name": "anthropic",
    "api_key": "sk-ant-..."
  },
  "agent": {
    "model": "anthropic/claude-sonnet-4-20250514"
  }
}
```

Supported model formats (via LiteLLM):
- `anthropic/claude-sonnet-4-20250514`
- `openai/gpt-4o`
- `groq/llama-3.3-70b-versatile`
- Any model string supported by [LiteLLM](https://docs.litellm.ai/docs/providers)

### 3. Chat with HuxBot

**Single message:**

```bash
huxbot agent -m "Hello!"
```

**Interactive mode:**

```bash
huxbot agent
```

### 4. Check status

```bash
huxbot status
```

## Chat Channels

### Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather) and get the token
2. Edit `~/.huxbot/config.json`:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "123456:ABC-DEF...",
      "allow_from": ["your_telegram_user_id"]
    }
  }
}
```

3. Start the gateway:

```bash
huxbot gateway
```

### Discord

1. Create a bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Enable the **Message Content** intent
3. Configure:

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "token": "your-bot-token",
      "allow_from": ["your_discord_user_id"],
      "extra": {
        "intents": 513
      }
    }
  }
}
```

### WhatsApp

WhatsApp requires a Node.js bridge using [@whiskeysockets/baileys](https://github.com/WhiskeySockets/Baileys).

**Requirements:** Node.js 20+

#### 1. Install and build the bridge

```bash
cd nanobot-main/bridge
npm install
npm run build
```

#### 2. Configure WhatsApp in `~/.huxbot/config.json`

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "extra": {
        "bridge_url": "ws://localhost:3001"
      }
    }
  }
}
```

#### 3. Start the bridge (Terminal 1)

```bash
cd nanobot-main/bridge
npm start
```

A QR code will appear in the terminal. Scan it with **WhatsApp > Linked Devices > Link a Device**.

#### 4. Start the gateway (Terminal 2)

```bash
huxbot gateway
```

Messages sent to your WhatsApp number will now be handled by HuxBot.

## Built-in Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `write_file` | Write content to a file |
| `edit_file` | Replace text in a file |
| `list_dir` | List directory contents |
| `exec_command` | Execute shell commands |
| `web_search` | Search the web |
| `web_fetch` | Fetch a URL's content |
| `send_message` | Send messages to channels |
| `hardware_pin_mode` | Set a GPIO pin as INPUT/OUTPUT |
| `hardware_digital_read` | Read digital value from a pin |
| `hardware_digital_write` | Write digital value to a pin |
| `hardware_analog_read` | Read analog value from a pin |
| `hardware_servo_write` | Move a servo to a given angle |
| `hardware_read_sensor` | Read a named sensor |
| `hardware_capture_image` | Capture a photo from the board camera |

> Hardware tools are only loaded when `hardware.enabled` is `true` in the config. See [Hardware Control](#hardware-control) below.

## Hardware Control

HuxBot can control Arduino and ESP32 boards over USB serial or WiFi. The LLM can interact with GPIO pins, servos, sensors, and cameras through natural language.

### Installation

Install with the `hardware` extra to pull in serial support:

```bash
pip install -e ".[hardware]"
```

### Configuration

Add a `hardware` section to `~/.huxbot/config.json`:

**USB serial (Arduino/ESP32 over USB):**

```json
{
  "hardware": {
    "enabled": true,
    "transport": "serial",
    "port": "/dev/ttyUSB0",
    "baudrate": 9600
  }
}
```

**WiFi (ESP32 with HTTP API):**

```json
{
  "hardware": {
    "enabled": true,
    "transport": "network",
    "port": "http://192.168.1.100"
  }
}
```

### Board Protocol

The board firmware must speak a simple text protocol over serial or HTTP:

```
COMMAND:ARGS  →  OK:RESULT  or  ERR:MESSAGE
```

Examples:
- `PIN_MODE:13:OUTPUT` → `OK:OUTPUT`
- `DIGITAL_WRITE:13:1` → `OK:1`
- `ANALOG_READ:0` → `OK:512`
- `SERVO_WRITE:9:90` → `OK:90`
- `SENSOR_READ:dht11_temp` → `OK:23.5`
- `CAPTURE_IMAGE` → `OK:<base64 data>`
- `LIST_DEVICES` → `OK:led:13,servo:9,dht11:4`

For network transport, the board should expose a `POST /cmd` endpoint that accepts the command as the request body and returns the response as plain text.

## Workspace & Customization

The workspace directory contains files that shape HuxBot's behavior:

```
workspace/
├── SOUL.md          # HuxBot's personality and values
├── AGENTS.md        # Instructions and guidelines
├── memory/
│   └── MEMORY.md    # Long-term memory (persists across sessions)
└── skills/
    └── my-skill/
        └── SKILL.md # Custom skill definition
```

### Adding Skills

Create a `SKILL.md` file inside `skills/<skill-name>/`:

```markdown
---
name: my-skill
description: What this skill does
trigger: /my-skill
---

Instructions for HuxBot when this skill is activated...
```

## Project Structure

```
huxbot/
├── huxbot/
│   ├── agent/          # ADK integration, instruction builder, memory, skills
│   ├── bus/            # Async message bus (inbound/outbound queues)
│   ├── channels/       # Telegram, Discord, WhatsApp implementations
│   ├── cli/            # CLI commands (typer)
│   ├── config/         # Pydantic config schema and loader
│   ├── hardware/       # Arduino/ESP32 board control (serial & network)
│   ├── tools/          # Built-in tools (filesystem, shell, web, messaging, hardware)
│   ├── skills/         # Built-in skills
│   └── utils/          # Helpers
├── workspace/          # Default workspace templates
└── tests/
```

## CLI Reference

```
huxbot onboard              # Initialize config and workspace
huxbot agent -m "message"   # Send a single message
huxbot agent                # Interactive chat mode
huxbot gateway              # Start channels + message processor
huxbot status               # Show configuration status
```

## License

MIT

---

A product of **ArtemisaAI**.
