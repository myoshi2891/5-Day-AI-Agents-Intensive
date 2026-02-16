"""Factories for the enhanced currency agent stack."""

from __future__ import annotations

import logging

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

from .config import CODE_EXEC_MODEL, retry_config
from .tools import get_exchange_rate, get_fee_for_payment_method

logger = logging.getLogger(__name__)

ENHANCED_INSTRUCTION = """You are a smart currency conversion assistant. You must strictly follow these steps and use the available tools.

For any currency conversion request:

1. Get Transaction Fee: Use the get_fee_for_payment_method() tool to determine the transaction fee.
2. Get Exchange Rate: Use the get_exchange_rate() tool to get the currency conversion rate.
3. Error Check: After each tool call, you must check the "status" field in the response. If the status is "error", you must stop and clearly explain the issue to the user.
4. Calculate Final Amount: Use the fee percentage from step 1 and the exchange rate from step 2 to compute the final converted amount. Show your math explicitly.
5. Provide Detailed Breakdown: In your summary, you must:
    * State the final converted amount.
    * Explain how the result was calculated, including:
        * The fee percentage and the fee amount in the original currency.
        * The amount remaining after deducting the fee.
        * The exchange rate applied.
"""


def build_enhanced_currency_agent() -> LlmAgent:
    agent = LlmAgent(
        name="enhanced_currency_agent",
        model=Gemini(model=CODE_EXEC_MODEL, retry_options=retry_config),
        instruction=ENHANCED_INSTRUCTION,
        tools=[
            get_fee_for_payment_method,
            get_exchange_rate,
        ],
    )
    logger.info("Enhanced currency agent created")
    return agent


def build_enhanced_runner(agent: LlmAgent | None = None) -> InMemoryRunner:
    agent = agent or build_enhanced_currency_agent()
    logger.info("InMemoryRunner wired for enhanced agent")
    return InMemoryRunner(agent=agent)


__all__ = [
    "build_enhanced_currency_agent",
    "build_enhanced_runner",
    "ENHANCED_INSTRUCTION",
]
