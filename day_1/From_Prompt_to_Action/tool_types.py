"""Shared tool response typings."""

from __future__ import annotations

from typing import Callable, Literal, TypeAlias, TypedDict

class ToolSuccessResponse(TypedDict):
    status: Literal["success"]
    report: str


class ToolErrorResponse(TypedDict):
    status: Literal["error"]
    error_message: str


ToolResponse: TypeAlias = ToolSuccessResponse | ToolErrorResponse

Tool = Callable[..., ToolResponse]
