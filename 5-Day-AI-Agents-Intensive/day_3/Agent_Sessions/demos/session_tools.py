"""Session-state tooling demo helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.adk.tools.tool_context import ToolContext

from ..apps import stateful as _stateful
from ..config import retry_config
from ..storage import DEFAULT_DB_PATH

SESSION_TOOLS_DEMO_NAME = "session-tools"
USER_NAME_SCOPE_LEVELS = ("temp", "user", "app")


@dataclass
class SessionToolsBundle:
    """Container bundling the agent, runner, and session service for the demo."""

    agent: LlmAgent
    runner: Runner
    session_service: InMemorySessionService


def cleanup_demo_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Remove the packaged SQLite DB so the demo starts fresh."""

    if db_path.exists():
        try:
            db_path.unlink()
            print("✅ Cleaned up old database files")
        except OSError as exc:
            print(f"⚠️  Failed to remove database: {exc}")
    else:
        print("✅ No database files to clean up")


def save_userinfo(tool_context: ToolContext, user_name: str, country: str) -> Dict[str, Any]:
    """Persist the provided user information in session state."""

    _set_scoped_state_value(tool_context, "name", user_name, scope="user")
    _set_scoped_state_value(tool_context, "country", country, scope="user")
    return {"status": "success"}


def retrieve_userinfo(tool_context: ToolContext) -> Dict[str, Any]:
    """Retrieve the stored user name and country from session state."""

    user_name = _get_scoped_state_value(tool_context, "name", "Username not found")
    country = _get_scoped_state_value(tool_context, "country", "Country not found")
    return {"status": "success", "user_name": user_name, "country": country}


def build_session_tools_bundle(
    *,
    app_name: str | None = None,
    model_name: str = "gemini-2.5-flash-lite",
) -> SessionToolsBundle:
    """Construct an in-memory runner preloaded with the session tools."""

    service = InMemorySessionService()
    agent = LlmAgent(
        model=Gemini(model=model_name, retry_options=retry_config),
        name="text_chat_bot",
        description="A text chatbot with tools for managing the user's name and country.",
        tools=[save_userinfo, retrieve_userinfo],
    )
    runner = Runner(agent=agent, app_name=app_name or _stateful.APP_NAME, session_service=service)
    return SessionToolsBundle(agent=agent, runner=runner, session_service=service)


async def run_session_tools_demo(
    *,
    bundle: SessionToolsBundle | None = None,
    cleanup: bool = True,
    requests: Sequence[str] | None = None,
    primary_session_id: str = "state-demo-session",
    isolated_session_id: str = "new-isolated-session",
    global_service: BaseSessionService | None = None,
) -> SessionToolsBundle:
    """Run the sample conversation and print state for both sessions."""

    if cleanup:
        cleanup_demo_database()

    bundle = bundle or build_session_tools_bundle()
    demo_requests = list(
        requests
        or (
            "Hi there, how are you doing today? What is my name?",
            "My name is Sam. I'm from Poland.",
            "What is my name? Which country am I from?",
        )
    )

    print("✅ Agent with session state tools initialized!")

    await _stateful.run_session(
        bundle.runner,
        demo_requests,
        primary_session_id,
        session_service_override=bundle.session_service,
    )

    session = await bundle.session_service.get_session(
        app_name=bundle.runner.app_name,
        user_id=_stateful.USER_ID,
        session_id=primary_session_id,
    )
    print("Session State Contents:")
    print(session.state if session else {})
    print("\n🔍 Notice the 'user:name' and 'user:country' keys storing our data!")

    await _stateful.run_session(
        bundle.runner,
        ["Hi there, how are you doing today? What is my name?"],
        isolated_session_id,
        session_service_override=bundle.session_service,
    )

    session = await bundle.session_service.get_session(
        app_name=bundle.runner.app_name,
        user_id=_stateful.USER_ID,
        session_id=isolated_session_id,
    )
    print("New Session State:")
    print(session.state if session else {})

    if global_service is not None:
        global_session = await global_service.get_session(
            app_name=bundle.runner.app_name,
            user_id=_stateful.USER_ID,
            session_id=isolated_session_id,
        )
        print("Session fetched from exported session_service:")
        print(global_session.state if global_session else {})

    print(
        "\nNote: Depending on implementation, user-scoped state may be shared across sessions."
    )

    return bundle


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


def _scoped_key(key: str, scope: str) -> str:
    prefix = f"{scope}:"
    return key if key.startswith(prefix) else f"{prefix}{key}"


__all__ = [
    "SESSION_TOOLS_DEMO_NAME",
    "USER_NAME_SCOPE_LEVELS",
    "SessionToolsBundle",
    "build_session_tools_bundle",
    "cleanup_demo_database",
    "run_session_tools_demo",
    "save_userinfo",
    "retrieve_userinfo",
]
