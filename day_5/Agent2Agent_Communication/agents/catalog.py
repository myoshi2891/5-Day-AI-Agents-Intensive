"""Product catalog agent responsible for pricing/spec lookups."""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from ..config import MODEL_NAME, RETRY_CONFIG


def get_product_info(product_name: str) -> str:
    """Return catalog details for a supported product."""
    product_catalog = {
        "iphone 15 pro": "iPhone 15 Pro, $999, Low Stock (8 units), 128GB, Titanium finish",
        "samsung galaxy s24": "Samsung Galaxy S24, $799, In Stock (31 units), 256GB, Phantom Black",
        "dell xps 15": 'Dell XPS 15, $1,299, In Stock (45 units), 15.6" display, 16GB RAM, 512GB SSD',
        "macbook pro 14": 'MacBook Pro 14", $1,999, In Stock (22 units), M3 Pro chip, 18GB RAM, 512GB SSD',
        "sony wh-1000xm5": "Sony WH-1000XM5 Headphones, $399, In Stock (67 units), Noise-canceling, 30hr battery",
        "ipad air": 'iPad Air, $599, In Stock (28 units), 10.9" display, 64GB',
        "lg ultrawide 34": 'LG UltraWide 34" Monitor, $499, Out of Stock, Expected: Next week',
    }

    product_lower = product_name.lower().strip()
    if product_lower in product_catalog:
        return f"Product: {product_catalog[product_lower]}"

    available = ", ".join([p.title() for p in product_catalog.keys()])
    return f"Sorry, I don't have information for {product_name}. Available products: {available}"


def create_product_catalog_agent() -> LlmAgent:
    """Build the LLM agent exposed over A2A for catalog queries."""
    return LlmAgent(
        model=Gemini(model=MODEL_NAME, retry_options=RETRY_CONFIG),
        name="product_catalog_agent",
        description="External vendor's product catalog agent that provides product information and availability.",
        instruction="""
        You are a product catalog specialist from an external vendor.
        When asked about products, use the get_product_info tool to fetch data from the catalog.
        Provide clear, accurate product information including price, availability, and specs.
        If asked about multiple products, look up each one.
        Be professional and helpful.
        """,
        tools=[get_product_info],
    )
