"""Package entrypoints for the Agent Tools Best Practices demo."""

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


def get_available_agents() -> dict[str, object]:
    """Return both agents so a single runtime can manage them together."""
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
