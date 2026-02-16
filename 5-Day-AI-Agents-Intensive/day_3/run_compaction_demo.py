import argparse
import asyncio
import sys
from pathlib import Path

from google.adk.cli.utils import envs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the compaction demo")
    parser.add_argument(
        "--session-id",
        default="compaction_demo",
        help="Session identifier to use for the compaction run",
    )
    args = parser.parse_args()

    agents_dir = Path(__file__).parent
    envs.load_dotenv_for_agent("Agent_Sessions", str(agents_dir))

    from Agent_Sessions.agent import run_compaction_demo as _run_compaction_demo

    try:
        asyncio.run(_run_compaction_demo(session_id=args.session_id))
    except Exception as exc:
        print(f"Error running compaction demo: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
