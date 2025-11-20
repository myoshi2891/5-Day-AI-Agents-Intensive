"""Database-backed session helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from google.adk.events.event_actions import EventCompaction
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions.session import Session
from google.genai import types

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = _PACKAGE_ROOT / "my_agent_data.db"
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_PATH}"


class HydratingDatabaseSessionService(DatabaseSessionService):
    """DatabaseSessionService that rehydrates compaction payloads."""

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Any | None = None,
    ) -> Session | None:
        session = await super().get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            config=config,
        )
        return _rehydrate_compaction_events(session)


def _rehydrate_compaction_events(session: Session | None) -> Session | None:
    if not session or not getattr(session, "events", None):
        return session

    for event in session.events:
        actions = getattr(event, "actions", None)
        if not actions:
            continue
        compaction = getattr(actions, "compaction", None)
        hydrated = _hydrate_compaction(compaction)
        if hydrated:
            actions.compaction = hydrated
    return session


def _hydrate_compaction(compaction: EventCompaction | dict | None) -> EventCompaction | None:
    if compaction is None or isinstance(compaction, EventCompaction):
        return compaction
    if not isinstance(compaction, dict):
        return None

    compaction_dict = dict(compaction)
    compacted_content = compaction_dict.get("compacted_content") or compaction_dict.get(
        "compactedContent"
    )
    if isinstance(compacted_content, dict):
        compaction_dict["compacted_content"] = types.Content.model_validate(compacted_content)

    return EventCompaction.model_validate(compaction_dict)


def build_database_session_service(
    *, db_url: str | None = None
) -> BaseSessionService:
    """Return a DatabaseSessionService pointing at the package SQLite DB."""
    return HydratingDatabaseSessionService(db_url=db_url or DEFAULT_DB_URL)


def inspect_db_events(db_path: Path | None = None, summarize: bool = False) -> list[tuple]:
    """Dump or summarize the events table for manual debugging.

    Args:
        db_path: Optional override for the SQLite file.
        summarize: When True, print up to three condensed summaries (two lines each)
            describing the sessions stored in the table.
    """
    path = Path(db_path or DEFAULT_DB_PATH)
    if not path.exists():
        print(f"-> Database file does not exist yet: {path}")
        return []

    try:
        with sqlite3.connect(path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT app_name, session_id, author, content FROM events"
            )
            rows = cursor.fetchall()
            if not rows:
                print("-> No data found in 'events' table.")
            elif summarize:
                _print_summaries(rows)
            else:
                print("-> events columns: app_name, session_id, author, content")
                for each in rows:
                    print(each)
            return rows
    except sqlite3.OperationalError as exc:
        print(f"-> Database error: {exc}")
        print(
            "-> The 'events' table might not exist yet. Try running a session first."
        )
        return []


__all__ = [
    "DEFAULT_DB_PATH",
    "DEFAULT_DB_URL",
    "build_database_session_service",
    "inspect_db_events",
]
def _print_summaries(rows: list[tuple]) -> None:
    """Print up to three condensed session summaries."""
    summaries: dict[tuple[str, str], list[str]] = {}
    for app_name, session_id, author, content in rows:
        key = (app_name, session_id)
        summaries.setdefault(key, [])
        if len(summaries[key]) < 2:
            text = _extract_text(content)
            if text:
                summaries[key].append(f"{author}: {text}")

    print("-> Summaries (up to 3 sessions, 2 lines each):")
    for idx, ((app_name, session_id), lines) in enumerate(summaries.items()):
        print(f"[{app_name}] session_id={session_id}")
        for line in lines[:2]:
            print(f"   {line}")
        if idx >= 2:
            break


def _extract_text(content_blob: str) -> str:
    """Best-effort extraction of the first text snippet from JSON content."""
    import json

    try:
        payload = json.loads(content_blob) if isinstance(content_blob, str) else content_blob
    except json.JSONDecodeError:
        return str(content_blob)[:120]

    parts = payload.get("parts") if isinstance(payload, dict) else None
    if parts:
        for part in parts:
            text = part.get("text")
            if text:
                return text.strip()[:120]
    return str(payload)[:120]
