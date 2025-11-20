"""Compatibility entrypoint exposing the stateful agent and demos."""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any, Dict, Iterable

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext

from .apps import stateful as _stateful
from .config import retry_config
from .storage import DEFAULT_DB_PATH
from .workflows import compaction as _compaction

# Re-export core constants and helpers for backwards compatibility
APP_NAME = _stateful.APP_NAME
USER_ID = _stateful.USER_ID
MODEL_NAME = _stateful.MODEL_NAME
session_service = _stateful.session_service
root_agent = _stateful.root_agent
runner = _stateful.runner
run_session = _stateful.run_session
check_data_in_db = _stateful.check_data_in_db

# Compaction workflow utilities
research_app_compacting = _compaction.research_app_compacting
research_runner_compacting = _compaction.research_runner_compacting
log_compaction_summary = _compaction.log_compaction_summary
run_compaction_demo = _compaction.run_compaction_demo

# Define scope levels for state keys (following best practices)
USER_NAME_SCOPE_LEVELS = ("temp", "user", "app")


def _scoped_key(key: str, scope: str) -> str:
    prefix = f"{scope}:"
    return key if key.startswith(prefix) else f"{prefix}{key}"


def _set_scoped_state_value(
    tool_context: ToolContext, key: str, value: Any, *, scope: str = "user"
) -> None:
    tool_context.state[_scoped_key(key, scope)] = value


def _get_scoped_state_value(
    tool_context: ToolContext,
    key: str,
    default: Any,
    *,
    scope_levels: Iterable[str] = USER_NAME_SCOPE_LEVELS,
) -> Any:
    for scope in scope_levels:
        scoped = _scoped_key(key, scope)
        if scoped in tool_context.state:
            return tool_context.state[scoped]
    return default


def _cleanup_demo_database() -> None:
    """Remove the package SQLite DB to ensure a fresh start for the demo."""
    if DEFAULT_DB_PATH.exists():
        DEFAULT_DB_PATH.unlink()
    print("✅ Cleaned up old database files")


def save_userinfo(tool_context: ToolContext, user_name: str, country: str) -> Dict[str, Any]:
    """Persist the provided user information in session state."""
    _set_scoped_state_value(tool_context, "name", user_name, scope="user")
    _set_scoped_state_value(tool_context, "country", country, scope="user")
    return {"status": "success"}


def retrieve_userinfo(tool_context: ToolContext) -> Dict[str, Any]:
    """Retrieve the stored user name and country from session state."""
    user_name = _get_scoped_state_value(
        tool_context, "name", "Username not found", scope_levels=USER_NAME_SCOPE_LEVELS
    )
    country = _get_scoped_state_value(
        tool_context, "country", "Country not found", scope_levels=USER_NAME_SCOPE_LEVELS
    )
    return {"status": "success", "user_name": user_name, "country": country}


def _build_session_state_bundle() -> tuple[LlmAgent, Runner, InMemorySessionService]:
    """Construct an agent/runner/service trio for the session-tools demo."""
    service = InMemorySessionService()
    agent = LlmAgent(
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        name="text_chat_bot",
        description=(
            "A text chatbot with tools for managing the user's name and country."
        ),
        tools=[save_userinfo, retrieve_userinfo],
    )
    runner_instance = Runner(agent=agent, app_name=APP_NAME, session_service=service)
    return agent, runner_instance, service


_EXPERIMENT = os.getenv("AGENT_SESSIONS_DEMO")
if _EXPERIMENT == "session-tools":
    _demo_agent, _demo_runner, _demo_service = _build_session_state_bundle()
    root_agent = _demo_agent
    runner = _demo_runner
    session_service = _demo_service
    print("⚠️ Using session-tools demo bundle for ADK exports")


async def _demo_session_state_tools() -> None:
    """Run the session-state tooling demo end-to-end."""
    _cleanup_demo_database()

    _, demo_runner, demo_service = _build_session_state_bundle()
    print("✅ Agent with session state tools initialized!")

    await run_session(
        demo_runner,
        [
            "Hi there, how are you doing today? What is my name?",
            "My name is Sam. I'm from Poland.",
            "What is my name? Which country am I from?",
        ],
        "state-demo-session",
        session_service_override=demo_service,
    )

    session = await demo_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id="state-demo-session"
    )
    print("Session State Contents:")
    print(session.state if session else {})
    print("\n🔍 Notice the 'user:name' and 'user:country' keys storing our data!")

    await run_session(
        demo_runner,
        ["Hi there, how are you doing today? What is my name?"],
        "new-isolated-session",
        session_service_override=demo_service,
    )

    session = await demo_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id="new-isolated-session"
    )
    print("New Session State:")
    print(session.state if session else {})

    # Also fetch via the exported session_service for quick cross-session inspection.
    global_session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id="new-isolated-session"
    )
    print("Session fetched from exported session_service:")
    print(global_session.state if global_session else {})

    print(
        "\nNote: Depending on implementation, user-scoped state may be shared across sessions."
    )


async def _demo_stateful_session() -> None:
    await run_session(
        runner,
        [
            "Hi, I am Sam! What is the capital of United States?",
            "Hello! What is my name?",
        ],
        "test-db-session-01",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent Sessions demo runner")
    parser.add_argument(
        "--demo",
        choices=("session-tools", "stateful"),
        default="session-tools",
        help=(
            "Pick the demo to run. 'session-tools' shows session state tooling; 'stateful' "
            "runs the original persistent DB demo."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.demo == "stateful":
        asyncio.run(_demo_stateful_session())
    else:
        asyncio.run(_demo_session_state_tools())
