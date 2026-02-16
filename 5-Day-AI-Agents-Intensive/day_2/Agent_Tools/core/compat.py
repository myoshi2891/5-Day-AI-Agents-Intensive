"""Optional google-adk integration helpers."""

from __future__ import annotations

import importlib
import logging
from typing import Any, Protocol, Type, cast

from .agents import FallbackAgent

logger = logging.getLogger(__name__)


class BaseAgent(Protocol):
    """Structural Agent interface used by both ADK and fallback agents."""

    tools: Any

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...


def load_agent_class() -> Type[BaseAgent]:
    """Return the real google-adk Agent if available, otherwise fallback."""
    try:
        module = importlib.import_module("google.adk.agents")
        agent_cls = getattr(module, "Agent")
        logger.info("google.adk.agents.Agent successfully loaded")
        return cast(Type[BaseAgent], agent_cls)
    except (ImportError, AttributeError) as exc:
        logger.warning("google-adk Agent not available, using fallback. reason=%s", exc)
        return FallbackAgent


__all__ = ["BaseAgent", "load_agent_class"]
