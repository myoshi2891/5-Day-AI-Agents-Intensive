"""Async demo helpers for the Agent Memory consolidation showcase."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Iterable

from google.adk.events import Event
from google.adk.sessions import Session
from google.genai import types

from .core.setup import AppComponents

async def ensure_session(components: AppComponents, session_id: str, user_id: str) -> Session:
    try:
        return await components.session_service.create_session(
            app_name=components.app_name, user_id=user_id, session_id=session_id
        )
    except Exception:
        session = await components.session_service.get_session(
            app_name=components.app_name, user_id=user_id, session_id=session_id
        )
        if session is None:
            raise RuntimeError(f"Session '{session_id}' does not exist.")
        return session

async def run_session(
    components: AppComponents,
    runner_queries: Sequence[str] | str,
    session_id: str,
    *,
    user_id: str,
    auto_save: bool,
    runner_override: Runner | None = None,
) -> None:
    print(f"\n### Session: {session_id}")
    session = await ensure_session(components, session_id, user_id)
    queries = [runner_queries] if isinstance(runner_queries, str) else list(runner_queries)

    for query in queries:
        print(f"\nUser > {query}")
        query_content = types.Content(role="user", parts=[types.Part(text=query)])
        runner = runner_override or components.runner
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=query_content,
        ):
            if not (event.content and event.content.parts):
                continue
            if event.is_final_response():
                part = event.content.parts[0]
                text = getattr(part, "text", None)
                if text and text != "None":
                    print(f"Model > {text}")
            else:
                for part in event.content.parts:
                    fn_call = getattr(part, "function_call", None)
                    if fn_call and fn_call.name == "load_memory":
                        print("📀 Agent is loading past memory...")

    if auto_save:
        refreshed_session = await components.session_service.get_session(
            app_name=components.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        if refreshed_session is None:
            raise RuntimeError(f"Unable to refresh session '{session_id}' for consolidation.")
        await components.memory_consolidator.process_session(refreshed_session)

async def seed_demo_memory(components: AppComponents, transcripts: dict[str, Sequence[tuple[str, str]]]) -> None:
    for session_id, conversation in transcripts.items():
        session = Session(
            id=session_id,
            app_name=components.app_name,
            user_id=components.user_id,
            events=[_build_event(role, text) for role, text in conversation],
        )
        await components.memory_service.add_session_to_memory(session)

async def search_memory(components: AppComponents, query: str) -> None:
    search_response = await components.memory_service.search_memory(
        app_name=components.app_name,
        user_id=components.user_id,
        query=query,
    )
    print("\n🔍 Search Results:")
    print(f"  Found {len(search_response.memories)} relevant memories\n")
    for memory in search_response.memories:
        if not (memory.content and memory.content.parts):
            continue
        part = memory.content.parts[0]
        raw_text = getattr(part, "text", None)
        if not raw_text:
            continue
        print(f"  [{memory.author}]: {raw_text[:80]}...")


def _build_event(author: str, text: str) -> Event:
    return Event(
        author=author,
        content=types.Content(role=author, parts=[types.Part(text=text)]),
    )

__all__ = [
    "ensure_session",
    "run_session",
    "seed_demo_memory",
    "search_memory",
]
