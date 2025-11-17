"""Weather/time agent module with optional google-adk integration and graceful fallbacks."""

from __future__ import annotations

import importlib
import logging
from typing import Any, Iterable, List, Optional, Protocol, Type, cast

from .agents import FallbackAgent
from .tools import get_current_time, get_weather
from .tool_types import Tool

logger = logging.getLogger(__name__)


class BaseAgent(Protocol):
    """Structural Agent interface used for typing regardless of dependency availability."""

    tools: List[Tool]

    def __init__(
        self,
        *,
        name: str,
        model: str,
        description: str,
        instruction: str,
        tools: Optional[Iterable[Tool]] = None,
        **kwargs: Any,
    ) -> None:
        ...


def _load_agent_class() -> Type[BaseAgent]:
    """Return the real google-adk Agent if available, otherwise fallback."""
    try:
        module = importlib.import_module("google.adk.agents")
        agent_cls = getattr(module, "Agent")
        logger.info("google.adk.agents.Agent successfully loaded")
        return cast(Type[BaseAgent], agent_cls)
    except (ImportError, AttributeError) as e:
        logger.warning(
            "google-adk Agent not available, using fallback. reason=%s", e
        )
        return FallbackAgent


Agent: Type[BaseAgent] = _load_agent_class()
_root_agent: Optional[BaseAgent] = None


def get_root_agent() -> BaseAgent:
    """Get or create the root agent instance."""
    global _root_agent
    if _root_agent is None:
        _root_agent = Agent(
            name="weather_time_agent",
            model="gemini-2.0-flash",
            description=(
                "Agent to answer questions about the time and weather in a city."
            ),
            instruction=(
                "You are a helpful agent who can answer user questions "
                "about the time and weather in a city."
            ),
            tools=[get_weather, get_current_time],
        )
    return _root_agent


root_agent = get_root_agent()
