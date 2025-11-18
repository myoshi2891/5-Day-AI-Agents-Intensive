"""Google ADK entrypoint that always exposes a BaseAgent root_agent."""

from __future__ import annotations

import logging

from day_2.Agent_Tools.core.agents import FallbackAgent
from day_2.Agent_Tools.core.builders import build_enhanced_currency_agent
from day_2.Agent_Tools.core.config import CODE_EXEC_MODEL
from day_2.Agent_Tools.core.tools import (
    get_exchange_rate,
    get_fee_for_payment_method,
)

logger = logging.getLogger(__name__)


def _build_fallback_agent() -> FallbackAgent:
    logger.warning(
        "Falling back to deterministic agent because enhanced agent could not be built."
    )
    return FallbackAgent(
        name="currency_agent",
        model=CODE_EXEC_MODEL,
        instruction="""You are a smart currency conversion assistant.""",
        tools=[get_fee_for_payment_method, get_exchange_rate],
    )


try:
    root_agent = build_enhanced_currency_agent()
    logger.info("Enhanced currency agent instantiated for ADK CLI.")
except Exception as exc:  # pragma: no cover
    logger.error("Failed to construct enhanced agent (%s). Using fallback.", exc)
    root_agent = _build_fallback_agent()


__all__ = ["root_agent"]
