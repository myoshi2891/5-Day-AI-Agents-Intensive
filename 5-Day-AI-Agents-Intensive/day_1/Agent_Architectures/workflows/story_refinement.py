"""Story refinement loop driven by critique feedback."""

from __future__ import annotations

from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool

from ..config import build_model


def _exit_loop() -> dict[str, str]:
    """Signal that the refinement loop is complete."""
    return {
        "status": "approved",
        "message": "Story approved. Exiting refinement loop.",
    }


def build_story_refinement() -> SequentialAgent:
    """Return a SequentialAgent that iterates writer -> critic -> refiner."""

    initial_writer_agent = Agent(
        name="InitialWriterAgent",
        model=build_model(),
        instruction=(
            "Based on the user's prompt, write the first draft of a short story "
            "(around 100-150 words).\n"
            "Output only the story text, with no introduction or explanation."
        ),
        output_key="current_story",
    )

    critic_agent = Agent(
        name="CriticAgent",
        model=build_model(),
        instruction=(
            "You are a constructive story critic. Review the story provided below.\n"
            "Story: {current_story}\n\n"
            "Evaluate the story's plot, characters, and pacing.\n"
            "- If the story is well-written and complete, call the `exit_loop` function to approve it.\n"
            "- Otherwise, provide 2-3 specific, actionable suggestions for improvement."
        ),
        output_key="critique",
        tools=[FunctionTool(_exit_loop)],
    )

    refiner_agent = Agent(
        name="RefinerAgent",
        model=build_model(),
        instruction=(
            "You are a story refiner. You have a story draft and critique.\n\n"
            "Story Draft: {current_story}\n"
            "Critique: {critique}\n\n"
            "Your task is to rewrite the story draft to fully incorporate every "
            "suggestion from the critique. Assume the critique contains actionable "
            "feedback unless the critic already approved and called `exit_loop`."
        ),
        output_key="current_story",
    )

    return SequentialAgent(
        name="StoryRefinement",
        sub_agents=[initial_writer_agent, critic_agent, refiner_agent],
    )


def run_story_refinement(prompt: str) -> object:
    """Execute the story refinement workflow."""
    runner = InMemoryRunner(agent=build_story_refinement())
    return runner.run_debug(prompt)


__all__ = ["build_story_refinement", "run_story_refinement"]
