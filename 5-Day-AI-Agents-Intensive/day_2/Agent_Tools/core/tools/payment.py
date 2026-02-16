
from __future__ import annotations

import logging



from ..tool_types import ToolResponse

logger = logging.getLogger(__name__)

# Fee structure for payment methods
_FEE_DATABASE = {
    "platinum credit card": 0.02,  # 2%
    "gold debit card": 0.035,  # 3.5%
    "bank transfer": 0.01,  # 1%
}


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
    method_key = method.lower()
    fee = _FEE_DATABASE.get(method_key)

    if fee is not None:
        logger.info("Fee lookup successful for method: %s", method)
        return {"status": "success", "fee_percentage": fee}

    logger.warning("Fee lookup failed for method: %s", method)
    return {
        "status": "error",
        "error_message": f"Payment method '{method}' not found",
    }

print("✅ Fee lookup function created")
print(f"💳 Test: {get_fee_for_payment_method('platinum credit card')}")

__all__ = ["get_fee_for_payment_method"]
