#!/usr/bin/env python3
"""
SignalWire Barge Detection Demo
===============================

Demonstrates SignalWire's highly configurable barge (interruption) system
by hosting multiple AI agents on different routes, each with distinct
barge behavior. Call any agent to experience the difference firsthand.
Each agent can transfer the caller to any other agent so you can compare
barge modes within a single call.

Agents:
  /open-barge       - Wide-open interruption (low confidence, 1 word minimum)
  /guarded-barge    - Hard to interrupt (high confidence, 3+ words required)
  /keyword-barge    - Only barges on specific keywords via regex
  /no-barge         - Barge completely disabled - agent always finishes speaking
  /transparent      - Transparent barge: agent waits for you to finish, then responds
  /storyteller      - Storyteller that is hard to interrupt mid-story but easy between stories

Usage:
  pip install signalwire-agents python-dotenv
  python barge_demo.py

Each route serves SWML to the SignalWire platform. Point a phone number
or SIP endpoint at any route to experience the behavior.
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from signalwire_agents import AgentBase, AgentServer
from signalwire_agents.core.function_result import SwaigFunctionResult

load_dotenv()

# ---------------------------------------------------------------------------
# Agent registry — every agent advertises its route and a short description
# so the transfer tool knows what's available.
# ---------------------------------------------------------------------------
AGENTS = {
    "default":       {"route": "/default",       "spoken": "Default, the baseline with no custom barge settings"},
    "open_barge":    {"route": "/open-barge",    "spoken": "Open, very easy to interrupt"},
    "guarded_barge": {"route": "/guarded-barge", "spoken": "Guarded, hard to interrupt"},
    "keyword_barge": {"route": "/keyword-barge", "spoken": "Keyword, only specific words can interrupt"},
    "no_barge":      {"route": "/no-barge",      "spoken": "No Barge, completely uninterruptible"},
    "transparent":   {"route": "/transparent",   "spoken": "Transparent, waits for you to finish then responds"},
    "storyteller":   {"route": "/storyteller",    "spoken": "Storyteller, moderate barge with a crosstalk prompt"},
}


def _build_transfer_list(exclude_key: str) -> str:
    """Build a speakable list of agents the caller can transfer to."""
    lines = []
    for key, info in AGENTS.items():
        if key == exclude_key:
            continue
        lines.append(f"  - {info['spoken']}")
    return "\n".join(lines)


def _add_transfer_tool(agent: AgentBase, self_key: str) -> None:
    """
    Register a transfer_to_agent SWAIG function on *agent* that can
    hand the call off to any other agent in the demo.
    """
    valid_targets = [k for k in AGENTS if k != self_key]

    def handle_transfer(args, raw_data):
        target = args.get("agent", "").strip()
        if target not in AGENTS or target == self_key:
            return SwaigFunctionResult(
                f"Unknown agent '{target}'. Valid choices: {', '.join(valid_targets)}"
            )
        dest_route = AGENTS[target]["route"]
        dest_url = agent.get_full_url(endpoint=dest_route)
        return (
            SwaigFunctionResult(
                f"Transferring you to the {AGENTS[target]['spoken']} mode now.",
            )
            .swml_transfer(dest_url, "You've been transferred to a new barge mode. Introduce yourself, state your barge settings, and list the other available modes.")
        )

    agent.define_tool(
        name="transfer_to_agent",
        description=(
            "Transfer the caller to a different barge-demo agent so they can "
            "experience a different interruption mode. Available agents: "
            + ", ".join(f'"{k}"' for k in valid_targets)
        ),
        parameters={
            "agent": {
                "type": "string",
                "description": (
                    "The agent key to transfer to. One of: "
                    + ", ".join(valid_targets)
                ),
            }
        },
        handler=handle_transfer,
    )


def _add_common_setup(agent: AgentBase, self_key: str, settings_summary: str) -> None:
    """Shared setup applied to every agent: greeting, transfer tool, general personality."""
    _add_transfer_tool(agent, self_key)

    other_agents = _build_transfer_list(self_key)

    # Force the agent to speak immediately on connect, even after a transfer
    if self_key == "default":
        agent.set_params({
            "static_greeting": "Hey! Welcome to the SignalWire barge demo.",
        })
    else:
        agent.set_params({
            "static_greeting": f"You've been transferred to {settings_summary.split('—')[0].strip()} mode.",
        })

    agent.prompt_add_section("First Response", body=(
        "After your static greeting plays, immediately follow up by explaining: "
        + settings_summary + " Then list the other barge modes available:\n"
        + other_agents + "\n"
        "Ask which one they'd like to try, or let them know they can just chat."
    ))

    agent.prompt_add_section("Personality", body=(
        "You are friendly, conversational, and concise. You can talk about anything — "
        "you are not limited to discussing barge. If the caller wants to chat, "
        "just chat naturally. If they ask about your barge config, answer from what you "
        "already know. When they pick a mode, use transfer_to_agent."
    ))


# ---------------------------------------------------------------------------
# Default Agent - SignalWire default barge settings, entry point for the demo
# ---------------------------------------------------------------------------
class DefaultBargeAgent(AgentBase):

    def __init__(self):
        super().__init__(name="default-barge", route="/default")

        self.set_params({
            "ai_model": "gpt-4.1-nano",
            "end_of_speech_timeout": 1000,
            "attention_timeout": 30000,
            "wait_for_user": False,
        })

        self.set_prompt_llm_params(temperature=0.5, top_p=0.9)
        self.add_language("English", "en-US", "elevenlabs.rachel")
        self.add_hints(["barge", "interrupt", "SignalWire", "transfer", "demo"])

        _add_common_setup(self, "default",
            "You are on default SignalWire barge settings — no custom tuning. "
            "This is the out-of-the-box baseline."
        )


# ---------------------------------------------------------------------------
# Agent 1: Open Barge - Very easy to interrupt
# ---------------------------------------------------------------------------
class OpenBargeAgent(AgentBase):

    def __init__(self):
        super().__init__(name="open-barge", route="/open-barge")

        self.set_params({
            "enable_barge": True,
            "barge_confidence": 0.1,
            "barge_min_words": 1,
            "transparent_barge": False,
            "static_greeting_no_barge": False,
            "ai_model": "gpt-4.1-nano",
            "end_of_speech_timeout": 800,
            "attention_timeout": 30000,
            "wait_for_user": False,
        })

        self.set_prompt_llm_params(temperature=0.5, top_p=0.9, barge_confidence=0.1)
        self.add_language("English", "en-US", "elevenlabs.rachel")
        self.add_hints(["barge", "interrupt", "SignalWire"])

        _add_common_setup(self, "open_barge",
            "Open barge mode — barge_confidence is 0.1 and barge_min_words is 1. "
            "Even quiet or uncertain speech will interrupt you immediately."
        )


# ---------------------------------------------------------------------------
# Agent 2: Guarded Barge - Hard to interrupt
# ---------------------------------------------------------------------------
class GuardedBargeAgent(AgentBase):

    def __init__(self):
        super().__init__(name="guarded-barge", route="/guarded-barge")

        self.set_params({
            "enable_barge": "complete",
            "barge_confidence": 0.85,
            "barge_min_words": 3,
            "transparent_barge": False,
            "static_greeting_no_barge": True,
            "ai_model": "gpt-4.1-nano",
            "end_of_speech_timeout": 1200,
            "attention_timeout": 30000,
            "wait_for_user": False,
        })

        self.set_prompt_llm_params(temperature=0.3, top_p=0.9, barge_confidence=0.85)
        self.add_language("English", "en-US", "elevenlabs.rachel")
        self.add_hints(["barge", "interrupt", "guarded", "SignalWire"])

        _add_common_setup(self, "guarded_barge",
            "Guarded barge mode — barge_confidence is 0.85 and barge_min_words is 3. "
            "The caller needs to speak clearly and say at least three words to interrupt you."
        )


# ---------------------------------------------------------------------------
# Agent 3: Keyword Barge - Only specific phrases trigger interruption
# ---------------------------------------------------------------------------
class KeywordBargeAgent(AgentBase):

    def __init__(self):
        super().__init__(name="keyword-barge", route="/keyword-barge")

        self.set_params({
            "enable_barge": True,
            "barge_match_string": "(?i)(stop|cancel|hold on|wait|actually)",
            "barge_min_words": 1,
            "barge_confidence": 0.5,
            "transparent_barge": False,
            "ai_model": "gpt-4.1-nano",
            "end_of_speech_timeout": 1000,
            "attention_timeout": 30000,
            "wait_for_user": False,
        })

        self.set_prompt_llm_params(temperature=0.5, top_p=0.9, barge_confidence=0.5)
        self.add_language("English", "en-US", "elevenlabs.rachel")
        self.add_hints(["stop", "cancel", "hold on", "wait", "actually", "barge", "keyword"])

        _add_common_setup(self, "keyword_barge",
            "Keyword barge mode — only the words 'stop', 'cancel', 'hold on', 'wait', "
            "or 'actually' will interrupt you. Everything else is ignored via barge_match_string regex."
        )


# ---------------------------------------------------------------------------
# Agent 4: No Barge - Agent always finishes speaking
# ---------------------------------------------------------------------------
class NoBargeAgent(AgentBase):

    def __init__(self):
        super().__init__(name="no-barge", route="/no-barge")

        self.set_params({
            "enable_barge": False,
            "static_greeting_no_barge": True,
            "ai_model": "gpt-4.1-nano",
            "end_of_speech_timeout": 1500,
            "attention_timeout": 30000,
            "wait_for_user": False,
        })

        self.set_prompt_llm_params(temperature=0.3, top_p=0.85)
        self.add_language("English", "en-US", "elevenlabs.rachel")
        self.add_hints(["barge", "interrupt", "disabled", "SignalWire"])

        _add_common_setup(self, "no_barge",
            "No-barge mode — enable_barge is false. You cannot be interrupted at all. "
            "You will always finish your entire response before the caller's input is processed."
        )


# ---------------------------------------------------------------------------
# Agent 5: Transparent Barge - Waits for caller to finish, then responds
# ---------------------------------------------------------------------------
class TransparentBargeAgent(AgentBase):

    def __init__(self):
        super().__init__(name="transparent-barge", route="/transparent")

        self.set_params({
            "enable_barge": "complete,partial",
            "transparent_barge": True,
            "transparent_barge_max_time": 5000,
            "barge_confidence": 0.5,
            "ai_model": "gpt-4.1-nano",
            "end_of_speech_timeout": 1000,
            "attention_timeout": 30000,
            "wait_for_user": False,
        })

        self.set_prompt_llm_params(temperature=0.5, top_p=0.9, barge_confidence=0.5)
        self.add_language("English", "en-US", "elevenlabs.rachel")
        self.add_hints(["transparent", "barge", "interrupt", "SignalWire"])

        _add_common_setup(self, "transparent",
            "Transparent barge mode — when you talk over the agent, it stops, waits for you "
            "to finish, then responds cleanly. The interrupted partial output is scrubbed "
            "from the conversation log. transparent_barge_max_time is 5 seconds."
        )


# ---------------------------------------------------------------------------
# Agent 6: Storyteller - Dynamic barge with interrupt_prompt for crosstalk
# ---------------------------------------------------------------------------
class StorytellerAgent(AgentBase):

    def __init__(self):
        super().__init__(name="storyteller", route="/storyteller")

        self.set_params({
            "enable_barge": "complete",
            "barge_confidence": 0.7,
            "barge_min_words": 2,
            "transparent_barge": False,
            "interrupt_prompt": (
                "The caller has interrupted your story. Briefly acknowledge what "
                "they said, ask if they want you to continue the story or if they "
                "have a question. Be warm and natural about it."
            ),
            "ai_model": "gpt-4.1-nano",
            "end_of_speech_timeout": 1000,
            "attention_timeout": 30000,
            "wait_for_user": False,
        })

        self.set_prompt_llm_params(temperature=0.7, top_p=0.95, barge_confidence=0.7)
        self.add_language("English", "en-US", "elevenlabs.rachel")
        self.add_hints(["story", "tell me", "interrupt", "barge", "SignalWire"])

        _add_common_setup(self, "storyteller",
            "Storyteller mode — barge_confidence is 0.7, barge_min_words is 2, and a custom "
            "interrupt_prompt handles crosstalk gracefully. Single-word cues like 'uh-huh' "
            "won't interrupt. Try asking for a story and then interrupting mid-way."
        )


# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    server = AgentServer(host="0.0.0.0", port=3000)

    server.register(DefaultBargeAgent())
    server.register(OpenBargeAgent())
    server.register(GuardedBargeAgent())
    server.register(KeywordBargeAgent())
    server.register(NoBargeAgent())
    server.register(TransparentBargeAgent())
    server.register(StorytellerAgent())

    print("\n" + "=" * 60)
    print("  SignalWire Barge Detection Demo")
    print("=" * 60)
    print()
    print("  Agents (each can transfer to any other):")
    print("    /default        - Default barge settings (entry point)")
    print("    /open-barge     - Very easy to interrupt (confidence 0.1)")
    print("    /guarded-barge  - Hard to interrupt (confidence 0.85, 3+ words)")
    print("    /keyword-barge  - Only 'stop', 'cancel', 'hold on', etc.")
    print("    /no-barge       - Cannot be interrupted at all")
    print("    /transparent    - Transparent barge (waits, then responds)")
    print("    /storyteller    - Moderate barge with interrupt_prompt")
    print()
    print("  Point a SignalWire phone number or SIP endpoint at any route.")
    print("=" * 60 + "\n")

    server.run()
