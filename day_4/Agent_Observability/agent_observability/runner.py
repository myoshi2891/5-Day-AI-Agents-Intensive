"""Runner helpers for executing the observability demo."""

from __future__ import annotations

from typing import Iterable

from google.adk.runners import InMemoryRunner
from google.adk.plugins.logging_plugin import LoggingPlugin

from .agents import create_google_search_agent, create_research_agent
from .config import DEFAULT_QUERY
from .plugins import ConversationTracePlugin, CountInvocationPlugin


def build_runner(extra_plugins: Iterable = ()) -> InMemoryRunner:
    """Build an InMemoryRunner with the default agents and plugins."""
    search_agent = create_google_search_agent()
    research_agent = create_research_agent(search_agent)

    plugins = [
        ConversationTracePlugin(root_agent_name=research_agent.name),
        LoggingPlugin(),
        CountInvocationPlugin(),
        *extra_plugins,
    ]
    return InMemoryRunner(agent=research_agent, plugins=plugins)


async def run_observability_demo(query: str = DEFAULT_QUERY) -> None:
    """Execute the demo and stream the debug output."""
    runner = build_runner()
    print("🚀 Running agent with LoggingPlugin and CountInvocationPlugin...")
    print("📊 Watch the comprehensive logging output below:\n")
    await runner.run_debug(query)
