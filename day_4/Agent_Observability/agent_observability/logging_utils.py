"""Logging helpers for the observability demo."""

from __future__ import annotations

import logging
import os
from typing import Iterable

from .config import LOG_FILE_NAME, LOG_FILES, LOG_FORMAT


def _cleanup_logs(log_files: Iterable[str]) -> None:
    for log_file in log_files:
        try:
            os.remove(log_file)
            print(f"🧹 Cleaned up {log_file}")
        except FileNotFoundError:
            continue
        except OSError as exc:
            print(f"⚠️  Could not delete {log_file}: {exc}")


def configure_logging(clear_logs: bool = True) -> None:
    """Configure structured logging for the demo."""
    if clear_logs:
        _cleanup_logs(LOG_FILES)

    logging.basicConfig(
        filename=LOG_FILE_NAME,
        level=logging.DEBUG,
        format=LOG_FORMAT,
        force=True,
    )
    print("✅ Logging configured")
