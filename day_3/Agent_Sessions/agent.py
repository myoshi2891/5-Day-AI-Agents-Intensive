"""Root agent definition for the Agent Sessions demos."""

from __future__ import annotations

import asyncio

from google.adk.agents import Agent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions.base_session_service import BaseSessionService
from google.genai import types

from .config import DEFAULT_MODEL_NAME, retry_config
from .storage import (
    DEFAULT_DB_URL,
    build_database_session_service,
    inspect_db_events,
)

APP_NAME = "default"
USER_ID = "default"
MODEL_NAME = DEFAULT_MODEL_NAME

print("✅ ADK components imported successfully.")


def check_data_in_db() -> list[tuple]:
    """Inspect the underlying SQLite DB for debugging."""
    return inspect_db_events()


session_service: BaseSessionService = build_database_session_service()


async def run_session(
    runner_instance: Runner,
    user_queries: list[str] | str | None = None,
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

    if isinstance(user_queries, str):
        user_queries = [user_queries]

    for query in user_queries:
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


print("✅ Helper functions defined.")

root_agent = Agent(
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    name="text_chat_bot",
    description="A text chatbot",
)

runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

print("✅ Stateful agent initialized!")
print(f"   - Application: {APP_NAME}")
print(f"   - User: {USER_ID}")
print(f"   - Using persistent DB: {DEFAULT_DB_URL}")

# Optional: App wrapper showcasing events compaction to shrink session logs.
research_app_compacting = App(
    name="research_app_compacting",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,
        overlap_size=1,
    ),
)

compaction_session_service = build_database_session_service()
research_runner_compacting = Runner(
    app=research_app_compacting,
    session_service=compaction_session_service,
)


print("✅ Research App upgraded with Events Compaction!")


async def log_compaction_summary(session_id: str = "compaction_demo") -> None:
    """Check if the compaction workflow produced a summary event."""
    final_session = await compaction_session_service.get_session(
        app_name=research_runner_compacting.app_name,
        user_id=USER_ID,
        session_id=session_id,
    )

    if final_session is None:
        print(f"❌ No session found for id '{session_id}'. Run the demo first.")
        return

    events = getattr(final_session, "events", None)
    if not events:
        print(f"❌ Session '{session_id}' contains no events yet.")
        return

    print("--- Searching for Compaction Summary Event ---")
    for event in events:
        actions = getattr(event, "actions", None)
        compaction = getattr(actions, "compaction", None)
        if compaction:
            print("\n✅ SUCCESS! Found the Compaction Event:")
            print(f"  Author: {event.author}")
            print(f"  Details: {compaction}")
            return

    print("❌ No compaction event found. Try increasing the number of turns in the demo.")


async def run_compaction_demo(session_id: str = "compaction_demo") -> None:
    """Drive a conversation long enough to trigger compaction."""
    demo_queries = [
        "Summarize the latest AI research breakthroughs.",
        "Add details about robotics funding news.",
        "Include any notable healthcare innovations.",
        "Wrap it up with key takeaways for executives.",
    ]

    await run_session(
        research_runner_compacting,
        demo_queries,
        session_name=session_id,
        session_service_override=compaction_session_service,
    )

    await log_compaction_summary(session_id)


async def _demo_stateful_session() -> None:

    await run_session(
        runner,
        [
            "Hi, I am Sam! What is the capital of United States?",
            "Hello! What is my name?",
        ],
        "test-db-session-01",
    )


if __name__ == "__main__":
    asyncio.run(_demo_stateful_session())
