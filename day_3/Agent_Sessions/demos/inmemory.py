"""Demo helpers for running the Agent Sessions sample with in-memory storage."""

from __future__ import annotations

import asyncio

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from ..apps import stateful as _stateful
from ..config import DEFAULT_MODEL_NAME, retry_config


def build_inmemory_runner(
    model_name: str = DEFAULT_MODEL_NAME,
) -> tuple[Runner, InMemorySessionService]:
    """Return a runner and service combo that keeps history purely in memory."""
    service = InMemorySessionService()
    agent = Agent(
        model=Gemini(model=model_name, retry_options=retry_config),
        name="text_chat_bot",
        description="A text chatbot (in-memory demo)",
    )
    runner = Runner(agent=agent, app_name=_stateful.APP_NAME, session_service=service)
    return runner, service


async def demo_inmemory_session() -> None:
    """Kick off a quick interactive demo using the in-memory session backend."""
    try:
        runner, service = build_inmemory_runner()
        await _stateful.run_session(
            runner,
            [
                "Hi, I am Sam! What is the capital of United States?",
                "Hello! What is my name?",
            ],
            session_name="inmemory-demo-session",
            session_service_override=service,
        )
    except Exception as exc:
        print(f"Demo failed: {exc}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(demo_inmemory_session())
    except Exception as exc:
        print(f"Demo failed: {exc}")
        raise
