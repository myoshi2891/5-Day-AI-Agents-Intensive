"""Shared configuration helpers for the Agent Architecture demos."""

from __future__ import annotations

from google.adk.models.google_llm import Gemini
from google.genai import types

DEFAULT_MODEL_NAME = "gemini-2.0-flash-lite"

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=2,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


def build_model(model_name: str = DEFAULT_MODEL_NAME) -> Gemini:
    """Return a Gemini model pre-configured with the shared retry policy."""
    return Gemini(model=model_name, retry_options=retry_config)


__all__ = ["DEFAULT_MODEL_NAME", "retry_config", "build_model"]
