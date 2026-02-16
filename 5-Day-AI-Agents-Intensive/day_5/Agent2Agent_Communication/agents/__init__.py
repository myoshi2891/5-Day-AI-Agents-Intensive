"""Agent factory functions for the Agent-to-Agent Communication sample."""

from .catalog import create_product_catalog_agent
from .inventory import create_inventory_agent
from .shipping import create_shipping_agent

__all__ = [
    "create_product_catalog_agent",
    "create_inventory_agent",
    "create_shipping_agent",
]
