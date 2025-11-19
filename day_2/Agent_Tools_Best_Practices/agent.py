"""Generic ADK entrypoint that exposes the MCP image agent."""

from __future__ import annotations

from .tools import display_events, get_root_agent, run_debug_session

root_agent = get_root_agent()

print("✅ MCP Tool created")


def main() -> None:
    """Run the debug session when executed as a script."""
    events = run_debug_session()
    if events:
        display_events(events)


if __name__ == "__main__":
    main()
