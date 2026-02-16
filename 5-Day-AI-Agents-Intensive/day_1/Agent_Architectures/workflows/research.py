"""Simple research coordinator workflow using two sub-agents."""

from __future__ import annotations

from typing import Any

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, google_search

from ..config import build_model


def build_research_workflow() -> Agent:
    """Return an Agent that orchestrates research + summarization."""
    research_agent = Agent(
        name="ResearchAgent",
        model=build_model(),
        instruction=(
            "You are a specialized research agent. Your only job is to use the "
            "google_search tool to find 2-3 pieces of relevant information on the "
            "given topic and present the findings with citations."
        ),
        tools=[google_search],
        output_key="research_findings",
    )

    summarizer_agent = Agent(
        name="SummarizerAgent",
        model=build_model(),
        instruction=(
            "Read the provided research findings: {research_findings}\n"
            "Create a concise summary as a bulleted list with 3-5 key points."
        ),
        output_key="final_summary",
    )

    return Agent(
        name="ResearchCoordinator",
        model=build_model(),
        instruction=(
            "You are a research coordinator. Your goal is to answer the user's query "
            "by orchestrating a workflow.\n"
            "1. First, you MUST call the `ResearchAgent` tool to find relevant "
            "information on the topic provided by the user.\n"
            "2. Next, after receiving the research findings, you MUST call the "
            "`SummarizerAgent` tool to create a concise summary.\n"
            "3. Finally, present the final summary clearly to the user as your response."
        ),
        tools=[AgentTool(research_agent), AgentTool(summarizer_agent)],
    )


def run_research_workflow(query: str) -> Any:
    """Execute the research workflow for a given query.

    Returns:
        Debug results from the InMemoryRunner execution.
    """
    runner = InMemoryRunner(agent=build_research_workflow())
    return runner.run_debug(query)


__all__ = ["build_research_workflow", "run_research_workflow"]
