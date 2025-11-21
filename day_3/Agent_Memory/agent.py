"""Public entrypoint for the Agent Memory consolidation demos."""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Sequence

from google.adk.runners import Runner
from google.adk.sessions import Session

from .core.setup import (
    APP_NAME,
    MODEL_NAME,
    USER_ID,
    AppComponents,
    create_components,
    retry_config,
    save_memory_tool,
)
from .demos import ensure_session, run_session as _run_session, search_memory, seed_demo_memory as _seed_demo_memory

# Lazily create and expose all shared components for adk web / CLI discovery.
components: AppComponents = create_components()
app = components.app
runner = components.runner
root_agent = components.root_agent
session_service = components.session_service
memory_service = components.memory_service
memory_consolidator = components.memory_consolidator
auto_memory_plugin = components.memory_plugin

async def run_session(
    runner_instance: Runner,
    session_id: str,
    *,
    user_queries: Sequence[str] | str,
    user_id: str = USER_ID,
    auto_save_to_memory: bool = False,
) -> None:
    """Compatibility wrapper that matches the original notebook helpers."""
    queries = user_queries
    await _run_session(
        components,
        runner_queries=queries,
        session_id=session_id,
        user_id=user_id,
        auto_save=auto_save_to_memory,
        runner_override=runner_instance,
    )

async def run_color_memory_demo() -> None:
    await run_session(
        runner,
        session_id="color-session-01",
        user_queries="My favorite color is blue-green. Can you write a Haiku about it?",
        auto_save_to_memory=True,
    )
    await run_session(
        runner,
        session_id="color-session-02",
        user_queries="What is my favorite color?",
    )
    await search_color_preferences()

async def run_birthday_memory_demo() -> None:
    await run_session(
        runner,
        session_id="birthday-session-01",
        user_queries="My birthday is on March 15th.",
        auto_save_to_memory=True,
    )
    await run_session(
        runner,
        session_id="birthday-session-02",
        user_queries="When is my birthday?",
    )

async def run_auto_memory_demo() -> None:
    print("\n🚀 Auto Memory Demo: zero manual memory calls!")
    await run_session(
        runner,
        session_id="auto-save-test",
        user_queries="I gifted a new toy to my nephew on his 1st birthday!",
    )
    await run_session(
        runner,
        session_id="auto-save-test-2",
        user_queries="What did I gift my nephew?",
    )

async def save_session_to_memory(session_id: str, *, user_id: str = USER_ID) -> None:
    session = await components.session_service.get_session(
        app_name=components.app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        raise RuntimeError(f"Session '{session_id}' does not exist.")
    await components.memory_consolidator.process_session(session)

async def search_color_preferences(
    *, query: str = "What is the user's favorite color?"
) -> None:
    await search_memory(components, query)

async def seed_demo_memory() -> None:
    transcripts: dict[str, Sequence[tuple[str, str]]] = {
        "color-session-manual": (
            ("user", "My favorite color is blue-green."),
            ("model", "Thanks, I will remember your favorite color is blue-green."),
        ),
        "birthday-session-manual": (
            ("user", "My birthday is on March 15th."),
            ("model", "Noted! I will remember March 15th as your birthday."),
        ),
    }
    await _seed_demo_memory(components, transcripts)

async def ensure_session_exists(session_id: str, *, user_id: str = USER_ID) -> Session:
    return await ensure_session(components, session_id, user_id)

# CLI wiring ---------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent Memory demo runner")
    parser.add_argument(
        "--demo",
        choices=("birthday", "color", "auto"),
        default="birthday",
        help="Pick which memory walkthrough to run from the CLI.",
    )
    return parser.parse_args()

def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse_args()
    if args.demo == "color":
        asyncio.run(run_color_memory_demo())
    elif args.demo == "auto":
        asyncio.run(run_auto_memory_demo())
    else:
        asyncio.run(run_birthday_memory_demo())

if __name__ == "__main__":  # pragma: no cover
    _main()

__all__ = [
    "APP_NAME",
    "USER_ID",
    "MODEL_NAME",
    "retry_config",
    "memory_service",
    "session_service",
    "root_agent",
    "app",
    "runner",
    "run_session",
    "save_session_to_memory",
    "run_color_memory_demo",
    "run_birthday_memory_demo",
    "run_auto_memory_demo",
    "search_color_preferences",
    "save_memory_tool",
    "seed_demo_memory",
    "memory_consolidator",
    "auto_memory_plugin",
]
