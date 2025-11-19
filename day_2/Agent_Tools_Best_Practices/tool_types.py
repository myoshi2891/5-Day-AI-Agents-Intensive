"""Shared tool response typings."""

from __future__ import annotations

from typing import Callable, Literal, Protocol, TypeAlias, TypedDict

try:  # Optional google-adk dependency
    from google.adk.tools.base_tool import BaseTool as AdkBaseTool
    from google.adk.tools.base_toolset import BaseToolset as AdkBaseToolset
except Exception:  # pragma: no cover - used when google.adk isn't installed
    class AdkBaseTool(Protocol):
        """Minimal protocol used when google-adk BaseTool isn't available."""

        ...

    class AdkBaseToolset(Protocol):
        """Minimal protocol used when google-adk BaseToolset isn't available."""

        ...

class ToolSuccessResponse(TypedDict):
    status: Literal["success"]
    report: str


class ToolErrorResponse(TypedDict):
    status: Literal["error"]
    error_message: str


ToolResponse: TypeAlias = ToolSuccessResponse | ToolErrorResponse

Tool = Callable[..., ToolResponse]

AgentToolType: TypeAlias = Tool | AdkBaseTool | AdkBaseToolset
