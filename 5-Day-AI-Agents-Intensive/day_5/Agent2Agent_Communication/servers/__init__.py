"""ASGI entrypoints for uvicorn."""

from .catalog_server import app as catalog_app  # noqa: F401
from .inventory_server import app as inventory_app  # noqa: F401
from .shipping_server import app as shipping_app  # noqa: F401

__all__ = ["catalog_app", "inventory_app", "shipping_app"]
