"""Package entrypoints for the Agent Tools Best Practices demo."""

from typing import TypedDict

from .workflows.image import (
    get_root_agent as get_image_agent,
    root_agent as image_root_agent,
    run_debug_session,
)
from .workflows.shipping import (
    get_root_agent as get_shipping_agent,
    root_agent as shipping_root_agent,
    run_shipping_workflow,
    run_shipping_workflow_sync,
)

# Default exports used by ADK (image workflow).
root_agent = image_root_agent
get_root_agent = get_image_agent


class AvailableAgents(TypedDict):
    image: object
    shipping: object


def get_available_agents() -> AvailableAgents:
    """Return fresh agent instances so one runtime can manage both workflows."""
    return {
        "image": get_image_agent(),
        "shipping": get_shipping_agent(),
    }

__all__ = [
    "image_root_agent",
    "get_image_agent",
    "run_debug_session",
    "shipping_root_agent",
    "get_shipping_agent",
    "run_shipping_workflow",
    "run_shipping_workflow_sync",
    "get_available_agents",
    "root_agent",
    "get_root_agent",
]
