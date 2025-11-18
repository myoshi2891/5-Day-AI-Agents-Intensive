"""Shared configuration for Agent Tools demo."""

from __future__ import annotations

import os

from google.genai import types


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# Must use a Gemini variant that supports the built-in code executor.
CODE_EXEC_MODEL = os.getenv(
    "AGENT_TOOLS_MODEL_NAME",
    "gemini-1.5-flash",
)
USE_ENHANCED_AGENT = _env_flag("AGENT_TOOLS_USE_ENHANCED", default=True)
FORCE_FALLBACK = _env_flag("AGENT_TOOLS_FORCE_FALLBACK", default=False)
USE_ENHANCED_AGENT = USE_ENHANCED_AGENT and not FORCE_FALLBACK

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

__all__ = ["CODE_EXEC_MODEL", "retry_config", "USE_ENHANCED_AGENT", "FORCE_FALLBACK"]
