"""Top-level router agent that forwards queries to specialized workflows."""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools import AgentTool

from ..config import build_model
from .blog_pipeline import build_blog_pipeline
from .executive_briefing import build_executive_briefing
from .research import build_research_workflow
from .story_refinement import build_story_refinement


def build_workflow_router() -> Agent:
    """Return an Agent that selects the right workflow based on the prompt."""
    research_tool = AgentTool(build_research_workflow())
    blog_tool = AgentTool(build_blog_pipeline())
    exec_tool = AgentTool(build_executive_briefing())
    story_tool = AgentTool(build_story_refinement())

    return Agent(
        name="WorkflowRouter",
        model=build_model(),
        instruction=(
            "You coordinate several specialized workflows. For every user prompt:\n"
            "- Determine which workflow best satisfies the request.\n"
            "- Immediately call exactly one tool to execute that workflow (never wait "
            "for additional instructions or confirmations).\n"
            "- Do not say anything until the tool has finished. After it completes, "
            "use its direct output to craft the final response.\n"
            "- Never respond with only your workflow choice; every reply must include "
            "the workflow result from the tool you ran.\n\n"
            "Workflows:\n"
            "1. ResearchCoordinator – use for general research questions or when "
            "research questions or when the user just needs information.\n"
            "2. BlogPipeline – use when the user wants a blog post, outline, or "
            "blog post, outline, or article draft.\n"
            "3. ResearchSystem – use for daily briefings or when the user mentions "
            "briefings or when the user mentions tech/health/finance trends.\n"
            "4. StoryRefinement – use for creative writing requests such as short "
            "writing requests such as short stories.\n\n"
            "Always explain which workflow you chose before presenting the final "
            "answer."
        ),
        tools=[research_tool, blog_tool, exec_tool, story_tool],
    )


__all__ = ["build_workflow_router"]
