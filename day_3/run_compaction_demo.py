import asyncio
from pathlib import Path

from google.adk.cli.utils import envs

AGENTS_DIR = Path(__file__).parent
envs.load_dotenv_for_agent("Agent_Sessions", str(AGENTS_DIR))

from Agent_Sessions.agent import run_compaction_demo  # noqa: E402


def main() -> None:
    asyncio.run(run_compaction_demo())


if __name__ == "__main__":
    main()
