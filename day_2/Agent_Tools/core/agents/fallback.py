"""Fallback Agent implementation used when google-adk is unavailable."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence, Set

from ..tool_types import Tool, ToolErrorResponse, ToolResponse

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - typing helper import
    from google.adk.models.google_llm import Gemini

    ModelArg = str | Gemini
else:  # Runtime fallback so this module stays importable without google-adk.
    ModelArg = str


class FallbackAgent:
    """Fallback Agent so this module works without google-adk."""

    def __init__(
        self,
        *,
        name: str,
        model: ModelArg,
        instruction: str,
        tools: Optional[Iterable[Tool]] = None,
        tool_triggers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.model = model
        self.instruction = instruction
        self.tools: List[Tool] = list(tools or [])
        # Preserve arbitrary config so tests can inspect parity with real Agent kwargs.
        self.extra_config: Dict[str, Any] = dict(kwargs)
        # Minimal keyword->tool mapping used for string routing in non-LLM environments.
        self.tool_triggers: Dict[str, str] = tool_triggers or {
            "rate": "get_exchange_rate",
            "exchange": "get_exchange_rate",
            "convert": "get_exchange_rate",
            "fee": "get_fee_for_payment_method",
            "payment": "get_fee_for_payment_method",
        }
        self._tool_arg_requirements: Dict[str, Set[str]] = {
            "get_exchange_rate": {"base_currency", "target_currency"},
            "get_fee_for_payment_method": {"method"},
        }
        self._conversion_required_args: Sequence[str] = (
            "amount",
            "base_currency",
            "target_currency",
            "method",
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"FallbackAgent(name={self.name!r}, model={self.model!r})"

    def _missing_kwargs(self, tool_name: str, provided: Dict[str, Any]) -> List[str]:
        required = self._tool_arg_requirements.get(tool_name, set())
        return sorted(arg for arg in required if arg not in provided)

    def _filter_tool_kwargs(self, tool_name: str, provided: Dict[str, Any]) -> Dict[str, Any]:
        required = self._tool_arg_requirements.get(tool_name, set())
        return {key: provided[key] for key in required if key in provided}

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

    def _can_handle_conversion(self, provided: Dict[str, Any]) -> bool:
        return all(arg in provided for arg in self._conversion_required_args)

    def _handle_conversion(self, **kwargs: Any) -> ToolResponse:
        """Simulate the currency-agent reasoning path by invoking the tools sequentially."""
        try:
            amount = float(kwargs["amount"])
        except (TypeError, ValueError, KeyError):
            return ToolErrorResponse(
                status="error",
                error_message="Valid numeric 'amount' is required to calculate conversions.",
            )

        method = str(kwargs["method"])
        base_currency = str(kwargs["base_currency"])
        target_currency = str(kwargs["target_currency"])

        fee_response = self._call_tool(
            "get_fee_for_payment_method",
            **{"method": method},
        )
        if fee_response["status"] == "error":
            return fee_response

        fee_percentage = fee_response.get("fee_percentage")
        if not isinstance(fee_percentage, (int, float)):
            return ToolErrorResponse(
                status="error",
                error_message="Fee lookup did not return 'fee_percentage'.",
            )

        rate_response = self._call_tool(
            "get_exchange_rate",
            **{
                "base_currency": base_currency,
                "target_currency": target_currency,
            },
        )
        if rate_response["status"] == "error":
            return rate_response

        rate = rate_response.get("rate")
        if not isinstance(rate, (int, float)):
            return ToolErrorResponse(
                status="error",
                error_message="Exchange rate lookup did not return 'rate'.",
            )

        fee_amount = amount * fee_percentage
        amount_after_fee = amount - fee_amount
        converted_amount = amount_after_fee * rate

        base_code = base_currency.upper()
        target_code = target_currency.upper()
        report = (
            f"{amount:,.2f} {base_code} -> {converted_amount:,.2f} {target_code} "
            f"(fee {fee_percentage*100:.2f}% = {fee_amount:,.2f} {base_code}, "
            f"amount after fee {amount_after_fee:,.2f} {base_code}, rate {rate:.4f})"
        )
        return {
            "status": "success",
            "report": report,
            "rate": rate,
            "fee_percentage": fee_percentage,
        }

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
            missing = self._missing_kwargs(tool_name, kwargs)
            if missing:
                return ToolErrorResponse(
                    status="error",
                    error_message=f"{tool_name} requires parameters: {', '.join(missing)}.",
                )
            filtered_kwargs = self._filter_tool_kwargs(tool_name, kwargs)
            return self._call_tool(tool_name, **filtered_kwargs)

        if self._can_handle_conversion(kwargs):
            return self._handle_conversion(**kwargs)

        lowered = query.lower()

        for trigger, inferred_tool in self.tool_triggers.items():
            if trigger in lowered:
                missing = self._missing_kwargs(inferred_tool, kwargs)
                if missing:
                    return ToolErrorResponse(
                        status="error",
                        error_message=f"{inferred_tool} requires parameters: {', '.join(missing)}.",
                    )
                filtered_kwargs = self._filter_tool_kwargs(inferred_tool, kwargs)
                return self._call_tool(inferred_tool, **filtered_kwargs)

        logger.warning("FallbackAgent could not infer tool from query=%s", query)
        return ToolErrorResponse(
            status="error",
            error_message=(
                "FallbackAgent cannot infer which tool to use from the query. "
                "Specify tool_name explicitly."
            ),
        )


__all__ = ["FallbackAgent"]
