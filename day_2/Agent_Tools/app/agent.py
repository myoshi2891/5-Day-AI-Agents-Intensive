"""Currency conversion agent with google-adk and fallback support."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from google.genai.errors import ClientError

from ..core.agents import FallbackAgent
from ..core.builders import build_enhanced_currency_agent, build_enhanced_runner
from ..core.compat import BaseAgent, load_agent_class
from ..core.config import CODE_EXEC_MODEL, USE_ENHANCED_AGENT
from ..core.debug_utils import show_python_code_and_result
from ..core.tools import get_exchange_rate, get_fee_for_payment_method

if TYPE_CHECKING:  # pragma: no cover - typing helpers
    from google.adk.agents import LlmAgent
    from google.adk.runners import InMemoryRunner
else:  # pragma: no cover - best effort fallback for runtime
    LlmAgent = Any
    InMemoryRunner = Any

logger = logging.getLogger(__name__)
Agent = load_agent_class()
_enhanced_currency_agent: Optional[LlmAgent] = None
_enhanced_runner: Optional[InMemoryRunner] = None
_root_agent: Optional[BaseAgent] = None

FALLBACK_INSTRUCTION = """You are a smart currency conversion assistant.

For currency conversion requests:
1. Use `get_fee_for_payment_method()` to find transaction fees
2. Use `get_exchange_rate()` to get currency conversion rates
3. Check the "status" field in each tool's response for errors
4. Calculate the final amount after fees based on the output from `get_fee_for_payment_method` and `get_exchange_rate` methods and provide a clear breakdown.
5. First, state the final converted amount.
    Then, explain how you got that result by showing the intermediate amounts. Your explanation must include: the fee percentage and its
    value in the original currency, the amount remaining after the fee, and the exchange rate used for the final conversion.

If any tool returns status "error", explain the issue to the user clearly.
"""

def _build_fallback_agent() -> FallbackAgent:
    return FallbackAgent(
        name="currency_agent",
        model=CODE_EXEC_MODEL,
        instruction=FALLBACK_INSTRUCTION,
        tools=[get_fee_for_payment_method, get_exchange_rate],
    )


def _build_enhanced_agent() -> LlmAgent:
    return build_enhanced_currency_agent()


def _get_enhanced_agent_and_runner() -> tuple[LlmAgent, InMemoryRunner]:
    global _enhanced_currency_agent, _enhanced_runner
    if _enhanced_currency_agent is None:
        _enhanced_currency_agent = _build_enhanced_agent()
        _enhanced_runner = build_enhanced_runner(_enhanced_currency_agent)
        logger.info("Enhanced currency agent constructed lazily")
    assert _enhanced_runner is not None
    return _enhanced_currency_agent, _enhanced_runner


def get_root_agent() -> BaseAgent:
    """Get or create the root agent instance."""
    global _root_agent
    if _root_agent is None:
        # Check if Agent class is not the FallbackAgent class itself
        if USE_ENHANCED_AGENT and Agent is not FallbackAgent:
            try:
                _root_agent = _build_enhanced_agent()
                logger.info("Enhanced currency agent set as root agent")
            except Exception as exc:  # pragma: no cover - defensive failover
                logger.warning(
                    "Failed to build enhanced agent (%s). Using fallback agent.", exc
                )
                _root_agent = _build_fallback_agent()
        else:
            _root_agent = _build_fallback_agent()
            if not USE_ENHANCED_AGENT:
                logger.info("Enhanced agent disabled via config; using fallback.")
            else:
                logger.warning("google-adk Agent unavailable; using fallback.")
    return _root_agent



# Eagerly initialize the agent to expose a ready-to-use `root_agent` object
# for the ADK CLI and for simplified notebook usage. This follows a common
# pattern in the project where the agent module provides a pre-constructed agent.
root_agent = get_root_agent()


def run_sample_conversion(query: str) -> None:
    """Helper to manually exercise the agent when running this module directly."""
    if USE_ENHANCED_AGENT:
        try:
            _, runner = _get_enhanced_agent_and_runner()
            responses = runner.run_debug(query)
            show_python_code_and_result(responses)
            return
        except Exception as exc:  # pragma: no cover - depends on quota
            logger.error(
                "Enhanced agent run failed during sample conversion (%s): %s",
                type(exc).__name__, exc
            )
    logger.warning(
        "Enhanced agent unavailable. Provide structured kwargs to the fallback agent."
    )



if __name__ == "__main__":  # pragma: no cover
    run_sample_conversion(
        "Convert 1,250 USD to INR using a Bank Transfer. Show me the precise calculation."
    )
