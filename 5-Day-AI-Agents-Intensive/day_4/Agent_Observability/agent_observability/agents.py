"""Agent factory functions used by the demo."""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.google_search_tool import google_search

from .config import MODEL_NAME, RETRY_CONFIG
from .tools import count_papers


def create_google_search_agent() -> LlmAgent:
    """Create an agent that only performs Google searches."""
    return LlmAgent(
        name="google_search_agent",
        model=Gemini(model=MODEL_NAME, retry_options=RETRY_CONFIG),
        description="Searches for information using Google search",
        instruction="""Use the google_search tool to find information on the given topic.
Return the raw search results.""",
        tools=[google_search],
    )


def create_research_agent(search_agent: LlmAgent) -> LlmAgent:
    """Create the root agent that orchestrates search and counting."""
    return LlmAgent(
        name="research_paper_finder_agent",
        model=Gemini(model=MODEL_NAME, retry_options=RETRY_CONFIG),
        instruction="""Your task is to find research papers and count them. You must first ask the
google_search_agent for candidate papers, then run the count_papers tool and
return both the papers and the total count. After using every required tool,
ALWAYS craft a final summary message for the user that lists each paper as a
bulleted list and ends with the exact line 'Total papers found: X', where X is
the actual number returned by count_papers. Do not end the conversation
immediately after a tool call.""",
        tools=[AgentTool(agent=search_agent), count_papers],
    )
