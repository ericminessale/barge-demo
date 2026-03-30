# SignalWire Barge Detection Demo

Demonstrates SignalWire's highly configurable barge (interruption) system
by hosting multiple AI agents on different routes, each with distinct
barge behavior. Call any agent to experience the difference firsthand.
Each agent can transfer the caller to any other agent so you can compare
barge modes within a single call.

## Agents

| Route | Behavior |
|-------|----------|
| `/open-barge` | Wide-open interruption (low confidence, 1 word minimum) |
| `/guarded-barge` | Hard to interrupt (high confidence, 3+ words required) |
| `/keyword-barge` | Only barges on specific keywords via regex |
| `/no-barge` | Barge completely disabled - agent always finishes speaking |
| `/transparent` | Transparent barge: agent waits for you to finish, then responds |
| `/storyteller` | Hard to interrupt mid-story but easy between stories |

## Prerequisites

- Python 3.10+
- A SignalWire account
- [ngrok](https://ngrok.com/) (for local development)

## Setup

1. Install dependencies:

```bash
pip install signalwire-agents python-dotenv
```

2. Copy `.env.example` to `.env` and configure:

```bash
SWML_BASIC_AUTH_USER=signalwire
SWML_BASIC_AUTH_PASSWORD=changeme
SWML_PROXY_URL_BASE=https://your-ngrok-url.ngrok-free.app
```

3. Start an ngrok tunnel:

```bash
ngrok http 3000
```

4. Run the demo:

```bash
python barge_demo.py
```

5. In your SignalWire Dashboard, point a phone number or SIP endpoint at a route using basic auth credentials in the URL:

```
https://signalwire:changeme@your-ngrok-url.ngrok-free.app/open-barge
```

Each route serves SWML to the SignalWire platform.

## Tech Stack

- **SignalWire AI Agents SDK** (`signalwire_agents`) - agent framework and SWML generation
- **FastAPI / Uvicorn** - web server
- **ElevenLabs** - TTS (rachel voice)
- **GPT-4.1-nano** - LLM
