"""Entry point for the Agent Observability demo."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Any, Optional

from google.adk.agents import LlmAgent

from .agent_observability import (
    DEFAULT_QUERY,
    configure_logging,
    run_observability_demo,
)
from .agent_observability.agents import (
    create_google_search_agent,
    create_research_agent,
)

_root_agent: Optional[LlmAgent] = None
_root_agent_lock = threading.Lock()


def get_root_agent() -> LlmAgent:
    """Return the root agent expected by Google ADK entrypoints."""
    global _root_agent
    if _root_agent is not None:
        return _root_agent

    with _root_agent_lock:
        if _root_agent is None:
            try:
                search_agent = create_google_search_agent()
                _root_agent = create_research_agent(search_agent)
            except Exception:
                logging.exception(
                    "Failed to initialize Agent Observability root_agent"
                )
                raise

    return _root_agent


def __getattr__(name: str) -> Any:
    """Expose root_agent lazily when imported by Google ADK."""
    if name == "root_agent":
        return get_root_agent()
    raise AttributeError(name)


async def _run(query: str) -> None:
    await run_observability_demo(query)


def main(query: Optional[str] = None) -> None:
    configure_logging()
    resolved_query = query or os.environ.get("AGENT_QUERY") or DEFAULT_QUERY
    asyncio.run(_run(resolved_query))


if __name__ == "__main__":
    main()


__all__ = ["get_root_agent", "root_agent"]
