"""Compatibility entrypoint exposing the stateful agent and demos."""

from __future__ import annotations

import argparse
import asyncio
import os

from .apps import stateful as _stateful
from .demos import session_tools as _session_tools
from .workflows import compaction as _compaction

# Re-export core constants and helpers for backwards compatibility
APP_NAME = _stateful.APP_NAME
USER_ID = _stateful.USER_ID
MODEL_NAME = _stateful.MODEL_NAME
session_service = _stateful.session_service
root_agent = _stateful.root_agent
runner = _stateful.runner
run_session = _stateful.run_session
check_data_in_db = _stateful.check_data_in_db

# Expose session-tools utilities via this entrypoint as well
USER_NAME_SCOPE_LEVELS = _session_tools.USER_NAME_SCOPE_LEVELS
save_userinfo = _session_tools.save_userinfo
retrieve_userinfo = _session_tools.retrieve_userinfo

# Compaction workflow utilities
research_app_compacting = _compaction.research_app_compacting
research_runner_compacting = _compaction.research_runner_compacting
log_compaction_summary = _compaction.log_compaction_summary
run_compaction_demo = _compaction.run_compaction_demo


_EXPERIMENT = os.getenv("AGENT_SESSIONS_DEMO")
if _EXPERIMENT == _session_tools.SESSION_TOOLS_DEMO_NAME:
    _bundle = _session_tools.build_session_tools_bundle(app_name=APP_NAME)
    root_agent = _bundle.agent
    runner = _bundle.runner
    session_service = _bundle.session_service
    print("⚠️ Using session-tools demo bundle for ADK exports")


async def _demo_session_state_tools() -> None:
    """Run the session state tooling demo end-to-end."""

    await _session_tools.run_session_tools_demo(global_service=session_service)


async def _demo_stateful_session() -> None:
    await run_session(
        runner,
        [
            "Hi, I am Sam! What is the capital of United States?",
            "Hello! What is my name?",
        ],
        "test-db-session-01",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent Sessions demo runner")
    parser.add_argument(
        "--demo",
        choices=(_session_tools.SESSION_TOOLS_DEMO_NAME, "stateful"),
        default=_session_tools.SESSION_TOOLS_DEMO_NAME,
        help=(
            "Pick the demo to run. 'session-tools' shows session state tooling; 'stateful' "
            "runs the original persistent DB demo."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.demo == "stateful":
        asyncio.run(_demo_stateful_session())
    else:
        asyncio.run(_demo_session_state_tools())
