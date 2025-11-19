"""Fallback Agent implementation used when google-adk is unavailable."""

from __future__ import annotations

import logging
from typing import Any, Iterable, List, Optional

from ..tool_types import AgentToolType, ToolErrorResponse, ToolResponse

logger = logging.getLogger(__name__)


class FallbackAgent:
    """Fallback Agent so this module works without google-adk."""

    def __init__(
        self,
        *,
        name: str,
        model: Any,
        instruction: str,
        tools: Optional[Iterable[AgentToolType]] = None,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.model = model
        self.instruction = instruction
        self.tools: List[AgentToolType] = list(tools or [])
        self.extra_config = dict(kwargs)

    def __repr__(self) -> str:  # pragma: no cover
        return f"FallbackAgent(name={self.name!r}, model={self.model!r})"

    def run(
        self,
        query: str,
        *,
        tool_name: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResponse:
        """Return a helpful error since MCP toolsets require google-adk runtime."""
        logger.warning(
            "FallbackAgent invoked query=%s tool_name=%s kwargs=%s "
            "(google-adk unavailable)",
            query,
            tool_name,
            kwargs,
        )

        return ToolErrorResponse(
            status="error",
            error_message=(
                "google-adk is not available, so MCP tools cannot be invoked. "
                "Install google-adk and rerun the image assistant."
            ),
        )


__all__ = ["FallbackAgent"]
