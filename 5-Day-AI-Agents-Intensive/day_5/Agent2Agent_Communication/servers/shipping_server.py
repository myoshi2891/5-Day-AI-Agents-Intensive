"""ASGI app for the Shipping Agent."""

from google.adk.a2a.utils.agent_to_a2a import to_a2a

from ..agents.shipping import create_shipping_agent
from ..config import A2A_PORTS

app = to_a2a(create_shipping_agent(), port=A2A_PORTS["shipping"])
