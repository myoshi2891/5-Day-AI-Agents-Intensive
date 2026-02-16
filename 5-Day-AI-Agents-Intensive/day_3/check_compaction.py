import argparse
import asyncio
import sys
from pathlib import Path

from google.adk.cli.utils import envs


def main() -> None:
    parser = argparse.ArgumentParser(description="Check compaction summary")
    parser.add_argument(
        "session_id",
        nargs="?",
        default="compaction_demo",
        help="Session ID to inspect",
    )
    args = parser.parse_args()

    agents_dir = Path(__file__).parent
    envs.load_dotenv_for_agent("Agent_Sessions", str(agents_dir))

    from Agent_Sessions.agent import log_compaction_summary  # noqa: E402
    from Agent_Sessions.storage import DEFAULT_DB_URL  # noqa: E402

    print(f"Using DB: {DEFAULT_DB_URL}")
    try:
        asyncio.run(log_compaction_summary(args.session_id))
    except Exception as exc:
        print(f"Error running summary: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
