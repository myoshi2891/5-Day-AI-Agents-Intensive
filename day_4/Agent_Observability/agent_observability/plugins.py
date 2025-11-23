"""Custom plugins used in the observability demo."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Set

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.utils._debug_output import print_event
from google.genai import types


class CountInvocationPlugin(BasePlugin):
    """Counts agent and tool invocations for quick instrumentation."""

    def __init__(self) -> None:
        super().__init__(name="count_invocation")
        self.agent_count = 0
        self.llm_request_count = 0
        self._lock = asyncio.Lock()

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        async with self._lock:
            self.agent_count += 1
            current_count = self.agent_count
        logging.info("[Plugin] Agent run count: %s", current_count)

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> None:
        async with self._lock:
            self.llm_request_count += 1
            current_count = self.llm_request_count
        logging.info("[Plugin] LLM request count: %s", current_count)


class ConversationTracePlugin(BasePlugin):
    """Prints concise transcripts so ADK Web logs match run_debug output."""

    def __init__(self, *, root_agent_name: str) -> None:
        super().__init__(name="conversation_trace")
        self._root_agent_name = root_agent_name
        self._seen_sessions: Set[str] = set()
        self._lock = asyncio.Lock()

    async def on_user_message_callback(
        self,
        *,
        invocation_context,
        user_message: types.Content,
    ) -> Optional[types.Content]:
        """Mirror run_debug's session + user logging for the root agent only."""
        if (
            invocation_context.agent.name != self._root_agent_name
            or self._should_skip_logging(invocation_context)
        ):
            return None

        async with self._lock:
            session_id = invocation_context.session.id
            first_visit = session_id not in self._seen_sessions
            if first_visit:
                self._seen_sessions.add(session_id)

        if first_visit:
            print(f"\n ### Created new session: {session_id}")
        else:
            print(f"\n ### Continue session: {session_id}")

        rendered_message = self._render_user_message(user_message)
        if rendered_message:
            print(f"\nUser > {rendered_message}")

        return None

    async def on_event_callback(
        self, *, invocation_context, event
    ) -> Optional[None]:
        """Stream agent events using the official print helper."""
        if (
            invocation_context.agent.name != self._root_agent_name
            or self._should_skip_logging(invocation_context)
        ):
            return None

        print_event(event)
        return None

    def _render_user_message(self, content: Optional[types.Content]) -> str:
        """Flatten user content into a simple string."""
        if not content or not content.parts:
            return ""

        pieces: list[str] = []
        for part in content.parts:
            if part.text:
                pieces.append(part.text.strip())
            elif part.function_call:
                pieces.append(f"[function_call: {part.function_call.name}]")
            elif part.function_response:
                pieces.append(
                    f"[function_response: {part.function_response.name}]"
                )

        return " ".join(piece for piece in pieces if piece)

    def _should_skip_logging(self, invocation_context) -> bool:
        """Avoid duplicating run_debug output in the default CLI session."""
        session = invocation_context.session
        return (
            invocation_context.app_name == "InMemoryRunner"
            and getattr(session, "id", None) == "debug_session_id"
            and getattr(session, "user_id", None) == "debug_user_id"
        )
