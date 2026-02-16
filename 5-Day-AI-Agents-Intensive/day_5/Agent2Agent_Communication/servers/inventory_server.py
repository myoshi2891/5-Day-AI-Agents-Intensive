"""ASGI app for the Inventory Agent."""

from google.adk.a2a.utils.agent_to_a2a import to_a2a

from ..agents.inventory import create_inventory_agent
from ..config import A2A_PORTS

app = to_a2a(create_inventory_agent(), port=A2A_PORTS["inventory"])
