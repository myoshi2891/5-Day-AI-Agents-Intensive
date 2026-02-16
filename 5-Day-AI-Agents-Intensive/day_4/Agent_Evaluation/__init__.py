"""Ensure google.adk CLI can locate the root agent."""

from . import agent  # re-exported for ADK tooling

__all__ = ["agent"]
