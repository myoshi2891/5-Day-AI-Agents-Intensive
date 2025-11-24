"""Inventory agent that tracks stock levels and restocks."""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from ..config import MODEL_NAME, RETRY_CONFIG


def get_inventory_status(product_name: str) -> str:
    """Return inventory details for a supported product."""
    inventory = {
        "iphone 15 pro": {"stock": 8, "status": "Low Stock", "restock": "Arriving in 3 days"},
        "samsung galaxy s24": {"stock": 31, "status": "In Stock", "restock": "Stable supply"},
        "dell xps 15": {"stock": 45, "status": "In Stock", "restock": "Weekly shipment"},
        "macbook pro 14": {"stock": 22, "status": "In Stock", "restock": "Next refresh in 10 days"},
        "sony wh-1000xm5": {"stock": 67, "status": "In Stock", "restock": "Monthly replenishment"},
        "ipad air": {"stock": 28, "status": "In Stock", "restock": "Next shipment tomorrow"},
        "lg ultrawide 34": {"stock": 0, "status": "Out of Stock", "restock": "Next week"},
    }

    product_lower = product_name.lower().strip()
    if product_lower in inventory:
        info = inventory[product_lower]
        return (
            f"Inventory Report: {product_name.title()} - {info['status']} "
            f"({info['stock']} units). Next restock: {info['restock']}."
        )

    available = ", ".join([p.title() for p in inventory.keys()])
    return f"Inventory unavailable for {product_name}. Tracked products: {available}"


def create_inventory_agent() -> LlmAgent:
    """Build the LLM agent exposed over A2A for warehouse lookups."""
    return LlmAgent(
        model=Gemini(model=MODEL_NAME, retry_options=RETRY_CONFIG),
        name="inventory_agent",
        description="Warehouse agent that manages stock levels and restock expectations.",
        instruction="""
        You are responsible for providing up-to-date inventory information.
        Always call the get_inventory_status tool before replying so you can confirm stock counts
        and restock timelines. Include both pieces of information in your response.
        """,
        tools=[get_inventory_status],
    )
