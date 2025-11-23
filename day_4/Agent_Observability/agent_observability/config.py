"""Configuration values for the observability demo."""

from __future__ import annotations

from google.genai import types

LOG_FILES = ("logger.log", "web.log", "tunnel.log")
LOG_FILE_NAME = "logger.log"
LOG_FORMAT = "%(filename)s:%(lineno)s %(levelname)s:%(message)s"
DEFAULT_QUERY = "Find recent papers on quantum computing"
MODEL_NAME = "gemini-2.5-flash-lite"

RETRY_CONFIG = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)
