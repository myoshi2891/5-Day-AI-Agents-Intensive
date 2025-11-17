"""Fallback Agent implementation used when google-adk is unavailable."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional

from ..tool_types import Tool, ToolErrorResponse, ToolResponse

logger = logging.getLogger(__name__)


class FallbackAgent:
    """Fallback Agent so this module works without google-adk."""

    def __init__(
        self,
        *,
        name: str,
        model: str,
        description: str,
        instruction: str,
        tools: Optional[Iterable[Tool]] = None,
        tool_triggers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.model = model
        self.description = description
        self.instruction = instruction
        self.tools: List[Tool] = list(tools or [])
        # Preserve arbitrary config so tests can inspect parity with real Agent kwargs.
        self.extra_config: Dict[str, Any] = dict(kwargs)
        # Minimal keyword->tool mapping used for string routing in non-LLM environments.
        self.tool_triggers: Dict[str, str] = tool_triggers or {
            "weather": "get_weather",
            "time": "get_current_time",
        }
        self._city_required_tools = {"get_weather", "get_current_time"}

    def __repr__(self) -> str:  # pragma: no cover
        return f"FallbackAgent(name={self.name!r}, model={self.model!r})"

    def _call_tool(self, tool_name: str, **tool_kwargs: Any) -> ToolResponse:
        """Find a tool by __name__ and invoke it."""
        for tool in self.tools:
            if tool.__name__ == tool_name:
                logger.info(
                    "FallbackAgent calling tool=%s kwargs=%s", tool_name, tool_kwargs
                )
                try:
                    return tool(**tool_kwargs)
                except Exception as e:  # pragma: no cover - defensive path
                    logger.error(
                        "Tool invocation failed tool=%s error=%s",
                        tool_name,
                        e,
                        exc_info=True,
                    )
                    return ToolErrorResponse(
                        status="error",
                        error_message=f"Tool '{tool_name}' raised an exception: {e}",
                    )
        logger.warning("Tool not found tool=%s", tool_name)
        return ToolErrorResponse(
            status="error",
            error_message=f"Tool '{tool_name}' not found in agent tools.",
        )

    def run(
        self,
        query: str,
        *,
        tool_name: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResponse:
        """LLM-less dispatcher for manual testing using simple keyword triggers."""
        logger.info(
            "FallbackAgent.run called query=%s tool_name=%s kwargs=%s",
            query,
            tool_name,
            kwargs,
        )

        if tool_name:
            return self._call_tool(tool_name, **kwargs)

        lowered = query.lower()

        for trigger, tool_name in self.tool_triggers.items():
            if trigger in lowered:
                if tool_name in self._city_required_tools and "city" not in kwargs:
                    return ToolErrorResponse(
                        status="error",
                        error_message="city parameter is required for this query.",
                    )
                return self._call_tool(tool_name, **kwargs)

        logger.warning("FallbackAgent could not infer tool from query=%s", query)
        return ToolErrorResponse(
            status="error",
            error_message=(
                "FallbackAgent cannot infer which tool to use from the query. "
                "Specify tool_name explicitly."
            ),
        )


__all__ = ["FallbackAgent"]
