"""Generic ADK entrypoint that exposes the shipping agent workflow."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

try:
    from day_2.Agent_Tools_Best_Practices.workflows.shipping import (
        get_root_agent,
        run_shipping_workflow,
    )
except ImportError:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from day_2.Agent_Tools_Best_Practices.workflows.shipping import (  # type: ignore
        get_root_agent,
        run_shipping_workflow,
    )

root_agent = get_root_agent()

print("✅ Shipping Tool created")


async def run_demos() -> None:
    # Demo 1: small order auto-approved by the tool
    await run_shipping_workflow("Ship 3 containers to Singapore")

    # Demo 2: large order, simulate human APPROVE
    await run_shipping_workflow(
        "Ship 10 containers to Rotterdam",
        auto_approve=True,
    )

    # Demo 3: large order, simulate human REJECT
    await run_shipping_workflow(
        "Ship 8 containers to Los Angeles",
        auto_approve=False,
    )


def main() -> None:
    asyncio.run(run_demos())


if __name__ == "__main__":
    main()
