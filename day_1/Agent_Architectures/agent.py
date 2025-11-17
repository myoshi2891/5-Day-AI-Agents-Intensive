"""Public API surface for the Agent Architecture demos.

Each workflow lives in ``workflows/`` to keep responsibilities focused:

- ``run_research_workflow`` – research + summarization coordination
- ``run_blog_pipeline`` – outline → draft → edit sequential pipeline
- ``run_executive_briefing`` – parallel research synthesized into a briefing
- ``run_story_refinement`` – writer → critic → refiner loop for fiction drafts
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from google.adk.agents import Agent as GoogleAgent

from .config import DEFAULT_MODEL_NAME, build_model, retry_config
from .workflows import (
    build_blog_pipeline,
    build_executive_briefing,
    build_research_workflow,
    build_story_refinement,
    build_workflow_router,
    run_blog_pipeline,
    run_executive_briefing,
    run_research_workflow,
    run_story_refinement,
)

# Backwards-compatible default for ADK CLI discovery.
root_agent: "GoogleAgent" = build_workflow_router()

__all__ = [
    "DEFAULT_MODEL_NAME",
    "retry_config",
    "build_model",
    "root_agent",
    "build_research_workflow",
    "run_research_workflow",
    "build_blog_pipeline",
    "run_blog_pipeline",
    "build_executive_briefing",
    "run_executive_briefing",
    "build_story_refinement",
    "run_story_refinement",
    "build_workflow_router",
]
