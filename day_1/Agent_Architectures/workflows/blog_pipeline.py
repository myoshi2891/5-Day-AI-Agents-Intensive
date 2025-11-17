"""Sequential writing workflow (outline -> draft -> edit)."""

from __future__ import annotations

from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import InMemoryRunner

from ..config import build_model


def build_blog_pipeline() -> SequentialAgent:
    """Return a SequentialAgent that orchestrates outline, writing, and editing."""
    outline_agent = Agent(
        name="OutlineAgent",
        model=build_model(),
        instruction=(
            "Create a blog outline for the given topic with:\n"
            "1. A catchy headline\n"
            "2. An introduction hook\n"
            "3. 3-5 main sections with 2-3 bullet points for each\n"
            "4. A concluding thought"
        ),
        output_key="blog_outline",
    )

    writer_agent = Agent(
        name="WriterAgent",
        model=build_model(),
        instruction=(
            "Following this outline strictly: {blog_outline}\n"
            "Write a brief, 200 to 300-word blog post with an engaging and "
            "informative tone."
        ),
        output_key="blog_draft",
    )

    editor_agent = Agent(
        name="EditorAgent",
        model=build_model(),
        instruction=(
            "Edit this draft: {blog_draft}\n"
            "Your task is to polish the text by fixing any grammatical errors, "
            "improving the flow and sentence structure, and enhancing overall clarity."
        ),
        output_key="final_blog",
    )

    return SequentialAgent(
        name="BlogPipeline",
        sub_agents=[outline_agent, writer_agent, editor_agent],
    )


def run_blog_pipeline(topic: str) -> object:
    """Execute the blog pipeline for a given topic."""
    runner = InMemoryRunner(agent=build_blog_pipeline())
    return runner.run_debug(topic)


__all__ = ["build_blog_pipeline", "run_blog_pipeline"]
