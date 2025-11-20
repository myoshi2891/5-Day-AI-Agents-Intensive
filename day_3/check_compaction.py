import asyncio
from pathlib import Path

from google.adk.cli.utils import envs

AGENTS_DIR = Path(__file__).parent
envs.load_dotenv_for_agent("Agent_Sessions", str(AGENTS_DIR))

from Agent_Sessions.agent import log_compaction_summary  # noqa: E402
from Agent_Sessions.storage import DEFAULT_DB_URL  # noqa: E402


def main() -> None:
    print(f"Using DB: {DEFAULT_DB_URL}")
    asyncio.run(log_compaction_summary("compaction_demo"))


if __name__ == "__main__":
    main()
