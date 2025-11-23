"""Entry point for the Agent Observability demo."""

from __future__ import annotations

import asyncio
import os
from typing import Optional

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


def get_root_agent() -> LlmAgent:
    """Return the root agent expected by Google ADK entrypoints."""
    global _root_agent
    if _root_agent is None:
        search_agent = create_google_search_agent()
        _root_agent = create_research_agent(search_agent)
    return _root_agent


root_agent = get_root_agent()


async def _run(query: str) -> None:
    await run_observability_demo(query)


def main(query: Optional[str] = None) -> None:
    configure_logging()
    resolved_query = query or os.environ.get("AGENT_QUERY") or DEFAULT_QUERY
    asyncio.run(_run(resolved_query))


if __name__ == "__main__":
    main()
