"""Shipping agent that provides delivery estimates and tracking."""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from ..config import MODEL_NAME, RETRY_CONFIG


def get_shipping_info(request: str) -> str:
    """Return shipping estimate or tracking details."""
    shipping_estimates = {
        "new york": {"delivery": "2 business days", "carrier": "UPS Air", "cost": "$35"},
        "los angeles": {"delivery": "1 business day", "carrier": "FedEx Express", "cost": "$29"},
        "chicago": {"delivery": "3 business days", "carrier": "USPS Priority", "cost": "$24"},
        "seattle": {"delivery": "4 business days", "carrier": "UPS Ground", "cost": "$22"},
    }
    tracking_updates = {
        "ord12345": {
            "status": "Out for delivery",
            "eta": "Today by 7 PM",
            "carrier": "UPS",
            "last_scan": "Local facility - 7:15 AM",
        },
        "ord67890": {
            "status": "In transit",
            "eta": "Tomorrow",
            "carrier": "FedEx",
            "last_scan": "Memphis, TN - 2:40 AM",
        },
    }

    normalized = request.lower().strip()
    if normalized in tracking_updates:
        info = tracking_updates[normalized]
        return (
            f"Tracking Update for {request.upper()}: {info['status']}. "
            f"ETA: {info['eta']}. Carrier: {info['carrier']}. "
            f"Last scan: {info['last_scan']}."
        )

    if normalized in shipping_estimates:
        info = shipping_estimates[normalized]
        return (
            f"Shipping Estimate to {request.title()}: {info['delivery']} via {info['carrier']} "
            f"with estimated cost {info['cost']}."
        )

    destinations = ", ".join([d.title() for d in shipping_estimates.keys()])
    orders = ", ".join([o.upper() for o in tracking_updates.keys()])
    return (
        f"Shipping information unavailable for '{request}'. "
        f"Supported destinations: {destinations}. Trackable orders: {orders}."
    )


def create_shipping_agent() -> LlmAgent:
    """Build the LLM agent exposed over A2A for logistics questions."""
    return LlmAgent(
        model=Gemini(model=MODEL_NAME, retry_options=RETRY_CONFIG),
        name="shipping_agent",
        description="Shipping logistics agent that provides delivery estimates and tracking.",
        instruction="""
        You coordinate delivery logistics.
        Use the get_shipping_info tool with either a destination (city/region) to get estimates
        or an order ID (e.g., ORD12345) to fetch tracking updates. Always report carrier and ETA.
        """,
        tools=[get_shipping_info],
    )
