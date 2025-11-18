"""Shared tool response typings."""

from __future__ import annotations

from typing import Callable, Literal, NotRequired, Required, TypeAlias, TypedDict

class ToolSuccessResponse(TypedDict, total=False):
    status: Required[Literal["success"]]
    report: NotRequired[str]
    rate: NotRequired[float]
    fee_percentage: NotRequired[float]

class ToolErrorResponse(TypedDict, total=False):
    status: Required[Literal["error"]]
    error_message: NotRequired[str]

ToolResponse: TypeAlias = ToolSuccessResponse | ToolErrorResponse

Tool = Callable[..., ToolResponse]
