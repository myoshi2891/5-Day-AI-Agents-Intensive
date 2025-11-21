"""LLM-backed memory consolidation utilities."""

from __future__ import annotations

import json
import logging
from typing import Any

from google.adk.events import Event
from google.adk.memory import InMemoryMemoryService
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.sessions import Session
from google.genai import types

logger = logging.getLogger(__name__)

class MemoryConsolidator:
    """Condenses raw session transcripts into concise facts before storage."""

    SYSTEM_PROMPT = (
        "You are a memory consolidation engine. Given a chat transcript, extract only "
        "durable, user-specific facts (preferences, biographical details, commitments, "
        "allergies, promises, etc.). Discard greetings or any non-lasting chit-chat. "
        "Return a JSON array; each item must contain 'fact', and may include "
        "'details' and 'category'. If no durable facts exist, return an empty array."
    )

    MAX_TRANSCRIPT_CHARS = 4000

    def __init__(self, *, model: Gemini, memory_service: InMemoryMemoryService):
        self._model = model
        self._memory_service = memory_service

    async def process_session(self, session: Session) -> None:
        """Run consolidation and store the resulting session."""
        try:
            consolidated = await self._build_consolidated_session(session)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Memory consolidation failed (%s). Storing raw session instead.", exc,
                exc_info=True,
            )
            consolidated = session
        await self._memory_service.add_session_to_memory(consolidated)

    async def _build_consolidated_session(self, session: Session) -> Session:
        transcript = self._format_transcript(session)
        if not transcript.strip():
            return session

        facts = await self._extract_facts(transcript)
        if not facts:
            return session

        deduped = await self._dedupe_facts(session, facts)
        if not deduped:
            return session

        summary_lines = []
        for idx, fact in enumerate(deduped, 1):
            statement = fact.get("fact", "").strip()
            if not statement:
                continue
            line = f"{idx}. {statement}"
            if details := (fact.get("details") or "").strip():
                line += f" — {details}"
            if category := (fact.get("category") or "").strip():
                line += f" [{category}]"
            summary_lines.append(line)

        if not summary_lines:
            return session

        structured = json.dumps(deduped, ensure_ascii=False, indent=2)
        consolidated_event = Event(
            author="memory_consolidator",
            content=types.Content(
                role="assistant",
                parts=[
                    types.Part(text="Memory Consolidation Summary\n" + "\n".join(summary_lines)),
                    types.Part(text="Structured facts:\n" + structured),
                ],
            ),
        )

        return Session(
            id=f"{session.id}:memory",
            app_name=session.app_name,
            user_id=session.user_id,
            events=[consolidated_event],
        )

    def _format_transcript(self, session: Session) -> str:
        lines: list[str] = []
        for event in session.events:
            if not (event.content and event.content.parts):
                continue
            for part in event.content.parts:
                if part.text:
                    role = (event.content.role or event.author or "unknown").capitalize()
                    lines.append(f"{role}: {part.text.strip()}")
                    break
        transcript = "\n".join(lines)
        if len(transcript) > self.MAX_TRANSCRIPT_CHARS:
            transcript = transcript[-self.MAX_TRANSCRIPT_CHARS :]
        return transcript

    async def _extract_facts(self, transcript: str) -> list[dict[str, Any]]:
        llm_request = LlmRequest(
            model=self._model.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            text=(
                                "Conversation transcript:\n"
                                f"{transcript}\n\n"
                                "List the durable facts now."
                            )
                        )
                    ],
                )
            ],
        )
        llm_request.config.system_instruction = self.SYSTEM_PROMPT
        llm_request.config.response_mime_type = "application/json"

        raw_response = ""
        async for llm_response in self._model.generate_content_async(llm_request):
            if llm_response.error_code:
                raise RuntimeError(
                    f"LLM consolidation failed: {llm_response.error_code} / {llm_response.error_message}"
                )
            if not (llm_response.content and llm_response.content.parts):
                continue
            for part in llm_response.content.parts:
                if part.text:
                    raw_response += part.text

        if not raw_response.strip():
            return []

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            logger.warning("LLM consolidation returned invalid JSON: %s", raw_response)
            return []

        facts: list[dict[str, Any]] = []
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    statement = (item.get("fact") or item.get("summary") or "").strip()
                    if not statement:
                        continue
                    details = (item.get("details") or item.get("explanation") or "").strip() or None
                    category = (item.get("category") or item.get("type") or "").strip() or None
                    facts.append({"fact": statement, "details": details, "category": category})
        return facts

    async def _dedupe_facts(self, session: Session, facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique: list[dict[str, Any]] = []
        for fact in facts:
            text = fact.get("fact")
            if not text:
                continue
            try:
                search_response = await self._memory_service.search_memory(
                    app_name=session.app_name,
                    user_id=session.user_id,
                    query=text,
                )
            except Exception:  # pragma: no cover - defensive search fallback
                unique.append(fact)
                continue

            duplicate = False
            for memory in search_response.memories or []:
                if not (memory.content and memory.content.parts):
                    continue
                for part in memory.content.parts:
                    if part.text and text.lower() in part.text.lower():
                        duplicate = True
                        break
                if duplicate:
                    break
            if not duplicate:
                unique.append(fact)
        return unique

__all__ = ["MemoryConsolidator"]
