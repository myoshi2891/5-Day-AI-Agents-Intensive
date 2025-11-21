"""App/component builders for the Agent Memory demos."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.apps.app import App
from google.adk.events import Event
from google.adk.memory import InMemoryMemoryService
from google.adk.models.google_llm import Gemini
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.tools import load_memory, preload_memory
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .memory_consolidation import MemoryConsolidator
from .plugins import AutoMemorySaverPlugin

APP_NAME = os.getenv(
    "AGENT_MEMORY_APP_NAME",
    Path(__file__).resolve().parents[1].name if "__file__" in globals() else "Agent_Memory",
)
USER_ID = os.getenv("AGENT_MEMORY_USER_ID", "demo_user")
MODEL_NAME = os.getenv("AGENT_MEMORY_MODEL_NAME", "gemini-2.5-flash-lite")

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

async def save_memory(tool_context: ToolContext, note: Optional[str] = None) -> dict[str, str]:
    """Persist the current session via the runner's configured memory service."""

    invocation = getattr(tool_context, "_invocation_context", None)
    if invocation is None or invocation.memory_service is None:
        return {
            "status": "error",
            "message": "Memory service is not available for this session.",
        }

    session_service = invocation.session_service
    session_id = invocation.session.id

    session = await session_service.get_session(
        app_name=invocation.app_name,
        user_id=invocation.user_id,
        session_id=session_id,
    )
    if session is None:
        session = invocation.session

    await invocation.memory_service.add_session_to_memory(session)
    details = "Current session stored in long-term memory."
    if note:
        details += f" Context: {note}"
    return {"status": "success", "message": details, "session_id": session_id}

save_memory_tool = FunctionTool(func=save_memory)

def build_memory_agent(*, include_memory_tool: bool = True) -> LlmAgent:
    """Construct the base ADK agent used for the demos."""

    instruction = "Answer user questions in simple words."
    tools: list = []
    if include_memory_tool:
        instruction += (
            " Use the save_memory tool to store personal facts whenever the user shares"
            " details (birthdays, preferences, etc.) or explicitly asks you to"
            " remember something, then confirm that the information was saved. Use"
            " load_memory when a question references earlier conversations, even if"
            " they happened in different sessions."
        )
        tools = [preload_memory, load_memory, save_memory_tool]

    return LlmAgent(
        model=Gemini(model=MODEL_NAME, retry_options=retry_config),
        name="MemoryDemoAgent",
        instruction=instruction,
        tools=tools,
    )

@dataclass(slots=True)
class AppComponents:
    app_name: str
    user_id: str
    model_name: str
    session_service: InMemorySessionService
    memory_service: InMemoryMemoryService
    memory_consolidator: MemoryConsolidator
    memory_plugin: BasePlugin
    root_agent: LlmAgent
    runner: Runner
    app: App

    def build_memory_event(self, author: str, text: str) -> Event:
        return Event(
            author=author,
            content=types.Content(role=author, parts=[types.Part(text=text)]),
        )

def create_components() -> AppComponents:
    """Create shared services, runner, and app with consolidation enabled."""

    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    root_agent = build_memory_agent()

    memory_consolidator = MemoryConsolidator(
        model=Gemini(model=MODEL_NAME, retry_options=retry_config),
        memory_service=memory_service,
    )
    memory_plugin = AutoMemorySaverPlugin(memory_consolidator)

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
        plugins=[memory_plugin],
    )

    app = App(
        name=APP_NAME,
        root_agent=root_agent,
        plugins=[memory_plugin],
    )

    return AppComponents(
        app_name=APP_NAME,
        user_id=USER_ID,
        model_name=MODEL_NAME,
        session_service=session_service,
        memory_service=memory_service,
        memory_consolidator=memory_consolidator,
        memory_plugin=memory_plugin,
        root_agent=root_agent,
        runner=runner,
        app=app,
    )

__all__ = [
    "APP_NAME",
    "USER_ID",
    "MODEL_NAME",
    "retry_config",
    "save_memory",
    "save_memory_tool",
    "build_memory_agent",
    "MemoryConsolidator",
    "AutoMemorySaverPlugin",
    "create_components",
    "AppComponents",
]
