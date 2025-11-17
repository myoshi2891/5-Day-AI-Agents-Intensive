"""Parallel research workflow summarized into an executive briefing."""

from __future__ import annotations

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search

from ..config import build_model


def _build_researcher(name: str, instruction: str, output_key: str) -> Agent:
    """Create a researcher agent with google_search tool and shared model config."""
    return Agent(
        name=name,
        model=build_model(),
        instruction=instruction,
        tools=[google_search],
        output_key=output_key,
    )


def build_executive_briefing(
    research_word_limit: int = 100,
    summary_word_limit: int = 200,
) -> SequentialAgent:
    """Return a SequentialAgent that runs parallel research then aggregates it."""
    research_limit_text = f"Keep the report concise (~{research_word_limit} words)."
    tech_researcher = _build_researcher(
        "TechResearcher",
        (
            "Research the latest AI/ML trends. Include 3 key developments, "
            "the main companies involved, and the potential impact. "
            f"{research_limit_text}"
        ),
        "tech_research",
    )

    health_researcher = _build_researcher(
        "HealthResearcher",
        (
            "Research recent medical breakthroughs. Include 3 significant advances, "
            "their practical applications, and estimated timelines. "
            f"{research_limit_text}"
        ),
        "health_research",
    )

    finance_researcher = _build_researcher(
        "FinanceResearcher",
        (
            "Research current fintech trends. Include 3 key trends, "
            "their market implications, and the future outlook. "
            f"{research_limit_text}"
        ),
        "finance_research",
    )

    parallel_research_team = ParallelAgent(
        name="ParallelResearchTeam",
        sub_agents=[tech_researcher, health_researcher, finance_researcher],
    )

    aggregator_agent = Agent(
        name="AggregatorAgent",
        model=build_model(),
        instruction=(
            "Combine these three research findings into a single executive summary:\n\n"
            "**Technology Trends:**\n"
            "{tech_research}\n\n"
            "**Health Breakthroughs:**\n"
            "{health_research}\n\n"
            "**Finance Innovations:**\n"
            "{finance_research}\n\n"
            "Your summary should highlight common themes, surprising connections, and "
            "the most important key takeaways from all three reports. "
            f"The final summary should be around {summary_word_limit} words."
        ),
        output_key="executive_summary",
    )

    return SequentialAgent(
        name="ResearchSystem",
        sub_agents=[parallel_research_team, aggregator_agent],
    )


def run_executive_briefing(
    prompt: str,
    *,
    research_word_limit: int = 100,
    summary_word_limit: int = 200,
) -> object:
    """Execute the executive briefing workflow."""
    runner = InMemoryRunner(
        agent=build_executive_briefing(
            research_word_limit=research_word_limit,
            summary_word_limit=summary_word_limit,
        )
    )
    return runner.run_debug(prompt)


__all__ = ["build_executive_briefing", "run_executive_briefing"]
