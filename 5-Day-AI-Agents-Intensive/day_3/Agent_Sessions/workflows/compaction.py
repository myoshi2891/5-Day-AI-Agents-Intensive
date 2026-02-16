"""Events compaction workflow helpers."""

from __future__ import annotations

from typing import Iterable

from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.runners import Runner

from ..apps.stateful import (
    APP_NAME,
    USER_ID,
    root_agent,
    run_session,
    session_service,
)
from ..storage import build_database_session_service

compaction_session_service = build_database_session_service()
research_app_compacting = App(
    name="research_app_compacting",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,
        overlap_size=1,
    ),
)
research_runner_compacting = Runner(
    app=research_app_compacting,
    session_service=compaction_session_service,
)


def describe_compaction_setup(verbose: bool = True) -> None:
    """Optionally log that the compaction-aware app is ready."""

    if verbose:
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


async def run_compaction_demo(
    *, session_id: str = "compaction_demo", queries: Iterable[str] | None = None
) -> None:
    """Drive a conversation long enough to trigger compaction."""
    demo_queries = queries or [
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


__all__ = [
    "research_app_compacting",
    "research_runner_compacting",
    "log_compaction_summary",
    "run_compaction_demo",
    "describe_compaction_setup",
]
