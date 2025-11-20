"""Stateful runner and helpers backed by a SQLite session service."""

from __future__ import annotations

import os
from typing import Iterable

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions.base_session_service import BaseSessionService
from google.genai import types

from ..config import DEFAULT_MODEL_NAME, retry_config
from ..storage import (
    DEFAULT_DB_URL,
    build_database_session_service,
    inspect_db_events,
)

APP_NAME = "default"
USER_ID = os.getenv("AGENT_SESSIONS_USER_ID", "default")
MODEL_NAME = DEFAULT_MODEL_NAME


def check_data_in_db(*, summarize: bool = False) -> list[tuple]:
    """Inspect the underlying SQLite DB for debugging."""
    return inspect_db_events(summarize=summarize)


session_service: BaseSessionService = build_database_session_service()


async def run_session(
    runner_instance: Runner,
    user_queries: Iterable[str] | str | None = None,
    session_name: str = "default",
    session_service_override: BaseSessionService | None = None,
) -> None:
    print(f"\n ### Session: {session_name}")

    app_name = runner_instance.app_name
    service = session_service_override or session_service

    try:
        session = await service.create_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )
    except Exception:
        session = await service.get_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )

    if session is None:
        raise RuntimeError("Session service returned no session instance.")

    if not user_queries:
        print("No queries!")
        return

    queries = [user_queries] if isinstance(user_queries, str) else list(user_queries)

    for query in queries:
        print(f"\nUser > {query}")
        query_content = types.Content(role="user", parts=[types.Part(text=query)])

        async for event in runner_instance.run_async(
            user_id=USER_ID, session_id=session.id, new_message=query_content
        ):
            if not event.content or not event.content.parts:
                continue
            part = event.content.parts[0]
            if part.text and part.text != "None":
                print(f"{MODEL_NAME} > ", part.text)


root_agent = Agent(
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    name="text_chat_bot",
    description="A text chatbot",
)

runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


def initialize(verbose: bool = True) -> None:
    """Optionally log initialization details for the stateful app."""

    if not verbose:
        return
    print("✅ ADK components imported successfully.")
    print("✅ Helper functions defined.")
    print("✅ Stateful agent initialized!")
    print(f"   - Application: {APP_NAME}")
    print(f"   - User: {USER_ID}")
    print(f"   - Using persistent DB: {DEFAULT_DB_URL}")


__all__ = [
    "APP_NAME",
    "USER_ID",
    "MODEL_NAME",
    "session_service",
    "runner",
    "root_agent",
    "run_session",
    "check_data_in_db",
    "initialize",
]
