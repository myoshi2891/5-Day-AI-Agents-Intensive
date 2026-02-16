"""ASGI app for the Product Catalog Agent."""

from google.adk.a2a.utils.agent_to_a2a import to_a2a

from ..agents.catalog import create_product_catalog_agent
from ..config import A2A_PORTS

app = to_a2a(create_product_catalog_agent(), port=A2A_PORTS["product_catalog"])
