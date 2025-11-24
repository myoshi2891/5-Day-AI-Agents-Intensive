"""Shared configuration for the Agent-to-Agent communication demo."""

from google.genai import types

# Common Gemini model name used across agents
MODEL_NAME = "gemini-2.0-flash-lite"

# Retry strategy reused by every agent to handle transient GenAI errors
RETRY_CONFIG = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Ports that each local A2A agent will use
A2A_PORTS = {
    "product_catalog": 8001,
    "inventory": 8002,
    "shipping": 8003,
}

# Human-friendly labels for log messages
A2A_LABELS = {
    "product_catalog": "Product Catalog Agent",
    "inventory": "Inventory Agent",
    "shipping": "Shipping Agent",
}

# Fully qualified server modules so uvicorn can import each ASGI app directly
A2A_SERVER_MODULES = {
    "product_catalog": "day_5.Agent2Agent_Communication.servers.catalog_server",
    "inventory": "day_5.Agent2Agent_Communication.servers.inventory_server",
    "shipping": "day_5.Agent2Agent_Communication.servers.shipping_server",
}

# Canonical sub-agent names exposed through RemoteA2aAgent
A2A_REMOTE_NAMES = {
    "product_catalog": "product_catalog_agent",
    "inventory": "inventory_agent",
    "shipping": "shipping_agent",
}
