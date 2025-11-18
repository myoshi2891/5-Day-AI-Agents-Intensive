from __future__ import annotations

import logging

try:
    import requests  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

from ..tool_types import ToolResponse

logger = logging.getLogger(__name__)

# Pay attention to the docstring, type hints, and return value.
def get_fee_for_payment_method(method: str) -> ToolResponse:
    """
    Looks up the transaction fee percentage for a given payment method.

    This tool simulates looking up a company's internal fee structure based on
    the name of the payment method provided by the user.

    Args:
        method: The name of the payment method. It should be descriptive,
                e.g., "platinum credit card" or "bank transfer".

    Returns:
        Dictionary with status and fee information.
        Success: {"status": "success", "fee_percentage": 0.02}
        Error: {"status": "error", "error_message": "Payment method not found"}
    """
    # This simulates looking up a company's internal fee structure.
    fee_database = {
        "platinum credit card": 0.02,  # 2%
        "gold debit card": 0.035,  # 3.5%
        "bank transfer": 0.01,  # 1%
    }

    fee = fee_database.get(method.lower())
    if fee is not None:
        return {"status": "success", "fee_percentage": fee}

    return {
        "status": "error",
        "error_message": f"Payment method '{method}' not found",
    }

print("✅ Fee lookup function created")
print(f"💳 Test: {get_fee_for_payment_method('platinum credit card')}")

__all__ = ["get_fee_for_payment_method"]
