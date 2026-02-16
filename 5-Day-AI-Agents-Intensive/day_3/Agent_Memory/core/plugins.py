"""Custom plugins used by the Agent Memory demos."""

from __future__ import annotations

from google.adk.agents.invocation_context import InvocationContext
from google.adk.plugins.base_plugin import BasePlugin

from .memory_consolidation import MemoryConsolidator

class AutoMemorySaverPlugin(BasePlugin):
    """Plugin that runs consolidation before persisting each session."""

    def __init__(self, consolidator: MemoryConsolidator):
        super().__init__(name="auto_memory_saver")
        self._consolidator = consolidator

    async def after_run_callback(self, *, invocation_context: InvocationContext) -> None:
        session = invocation_context.session
        if session is None:
            return
        await self._consolidator.process_session(session)

__all__ = ["AutoMemorySaverPlugin"]
