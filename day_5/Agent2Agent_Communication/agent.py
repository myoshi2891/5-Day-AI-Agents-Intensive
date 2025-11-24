"""Customer Support Agent orchestrating multiple remote A2A services."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
import warnings
from pathlib import Path
from typing import Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[2]

# When executed directly (python day_5/Agent2Agent_Communication/agent.py),
# ensure the repository root is on sys.path so package imports succeed.
if __package__ is None or __package__ == "":
    if str(REPO_ROOT) not in sys.path:
        sys.path.append(str(REPO_ROOT))

import requests  # noqa: E402
from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.agents.remote_a2a_agent import (  # noqa: E402
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)
from google.adk.models.google_llm import Gemini  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

if __package__:
    from .agents import (  # type: ignore[attr-defined]
        create_inventory_agent,
        create_product_catalog_agent,
        create_shipping_agent,
    )
    from .config import (  # type: ignore[attr-defined]
        A2A_LABELS,
        A2A_PORTS,
        A2A_REMOTE_NAMES,
        A2A_SERVER_MODULES,
        MODEL_NAME,
        RETRY_CONFIG,
    )
else:  # Fallback when running the script directly (python path/to/agent.py)
    from day_5.Agent2Agent_Communication.agents import (  # noqa: E402
        create_inventory_agent,
        create_product_catalog_agent,
        create_shipping_agent,
    )
    from day_5.Agent2Agent_Communication.config import (  # noqa: E402
        A2A_LABELS,
        A2A_PORTS,
        A2A_REMOTE_NAMES,
        A2A_SERVER_MODULES,
        MODEL_NAME,
        RETRY_CONFIG,
    )

warnings.filterwarnings("ignore")
print("✅ ADK components imported successfully.")

AGENT_KEYS: Iterable[str] = ("product_catalog", "inventory", "shipping")
SCENARIO_PROMPTS: List[str] = [
    "Can you tell me about the iPhone 15 Pro? Is it in stock and when would it ship to New York?",
    "I'm looking for a laptop. Compare the Dell XPS 15 and MacBook Pro 14, including availability.",
    "If I need a MacBook Pro 14 shipped to Chicago, what's the delivery estimate?",
    "A customer lost tracking for ORD12345. Can you let me know the latest shipping update?",
]

REMOTE_DESCRIPTIONS: Dict[str, str] = {
    "product_catalog": "Remote product catalog agent from external vendor that provides product information.",
    "inventory": "Remote inventory operations agent tracking stock and restock timelines.",
    "shipping": "Remote shipping logistics agent for delivery estimates and tracking.",
}

AGENT_BUILDERS = {
    "product_catalog": (create_product_catalog_agent, "get_product_info()"),
    "inventory": (create_inventory_agent, "get_inventory_status()"),
    "shipping": (create_shipping_agent, "get_shipping_info()"),
}


def wait_for_server(port: int, agent_label: str, retries: int = 30) -> bool:
    """Poll until an A2A server responds."""
    url = f"http://localhost:{port}{AGENT_CARD_WELL_KNOWN_PATH}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print(f"\n✅ {agent_label} server is running at http://localhost:{port}")
                return True
        except requests.exceptions.RequestException:
            time.sleep(5)
            print(".", end="", flush=True)
    print(f"\n⚠️  {agent_label} server may not be ready yet. Check manually if needed.")
    return False


def log_agent_card(port: int, agent_label: str) -> None:
    """Fetch and display the agent card for visibility."""
    try:
        response = requests.get(
            f"http://localhost:{port}{AGENT_CARD_WELL_KNOWN_PATH}", timeout=5
        )
        if response.status_code == 200:
            agent_card = response.json()
            print(f"\n📋 {agent_label} Agent Card:")
            print(json.dumps(agent_card, indent=2))
            print("\n✨ Key Information:")
            print(f"   Name: {agent_card.get('name')}")
            print(f"   Description: {agent_card.get('description')}")
            print(f"   URL: {agent_card.get('url')}")
            print(f"   Skills: {len(agent_card.get('skills', []))} capabilities exposed")
        else:
            print(f"❌ Failed to fetch agent card for {agent_label}: {response.status_code}")
    except requests.exceptions.RequestException as exc:
        print(f"❌ Error fetching agent card for {agent_label}: {exc}")


def start_a2a_server(agent_key: str) -> subprocess.Popen:
    """Start uvicorn for a given agent and wait for readiness."""
    module_path = A2A_SERVER_MODULES[agent_key]
    port = A2A_PORTS[agent_key]
    label = A2A_LABELS[agent_key]

    process = subprocess.Popen(
        [
            "uvicorn",
            f"{module_path}:app",
            "--host",
            "localhost",
            "--port",
            str(port),
        ],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ},
    )
    print(f"🚀 Starting {label} server on port {port}...")
    wait_for_server(port, label)
    log_agent_card(port, label)
    return process


def start_all_servers() -> List[subprocess.Popen]:
    """Spin up all specialized agents."""
    processes: List[subprocess.Popen] = []
    for agent_key in AGENT_KEYS:
        processes.append(start_a2a_server(agent_key))
    return processes


def shutdown_servers(processes: Iterable[subprocess.Popen]) -> None:
    """Terminate uvicorn processes gracefully."""
    for process in processes:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def build_remote_agents() -> Dict[str, RemoteA2aAgent]:
    """Create RemoteA2aAgent proxies for each specialized service."""
    remotes: Dict[str, RemoteA2aAgent] = {}
    for agent_key in AGENT_KEYS:
        remotes[agent_key] = RemoteA2aAgent(
            name=A2A_REMOTE_NAMES[agent_key],
            description=REMOTE_DESCRIPTIONS[agent_key],
            agent_card=f"http://localhost:{A2A_PORTS[agent_key]}{AGENT_CARD_WELL_KNOWN_PATH}",
        )
        print(
            f"✅ Remote {A2A_LABELS[agent_key]} proxy created at "
            f"http://localhost:{A2A_PORTS[agent_key]}"
        )
    return remotes


# Build the specialized agents (for documentation/logging purposes)
for agent_key, (builder, tool_name) in AGENT_BUILDERS.items():
    builder()
    print(f"✅ {A2A_LABELS[agent_key]} definition loaded (Tool: {tool_name})")

# Launch uvicorn servers so they can be accessed via A2A.
a2a_server_processes = start_all_servers()
globals()["a2a_server_processes"] = a2a_server_processes

# Create remote proxies and wire up the orchestrator.
remote_agents = build_remote_agents()
customer_support_agent = LlmAgent(
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_CONFIG),
    name="customer_support_agent",
    description="Customer support assistant coordinating product, inventory, and shipping requests.",
    instruction="""
    You are a friendly and professional customer support agent.

    Always coordinate with specialized sub-agents:
    1. Use product_catalog_agent for detailed specs, pricing, and comparisons.
    2. Use inventory_agent to confirm real-time stock counts and restock timelines.
    3. Use shipping_agent for delivery ETAs or tracking events (provide city or order ID).

    Combine their insights into a single coherent response for the customer.
    """,
    sub_agents=list(remote_agents.values()),
)

print("✅ Customer Support Agent created!")
print("   Model:", MODEL_NAME)
print("   Sub-agents: 3 (Product Catalog, Inventory, Shipping via A2A)")
root_agent = customer_support_agent


async def test_a2a_communication(user_query: str) -> None:
    """Exercise the Customer Support Agent over a single query."""
    session_service = InMemorySessionService()
    app_name = "support_app"
    user_id = "demo_user"
    session_id = f"demo_session_{uuid.uuid4().hex[:8]}"

    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    runner = Runner(agent=customer_support_agent, app_name=app_name, session_service=session_service)
    test_content = types.Content(parts=[types.Part(text=user_query)])

    print(f"\n👤 Customer: {user_query}")
    print("\n🎧 Support Agent response:")
    print("-" * 60)
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=test_content,
    ):
        if event.is_final_response() and event.content:
            parts = getattr(event.content, "parts", None) or []
            for part in parts:
                if hasattr(part, "text"):
                    print(part.text)
    print("-" * 60)


async def main() -> None:
    """Entry point when running this module as a script."""
    print("🧪 Testing A2A Communication...\n")
    for prompt in SCENARIO_PROMPTS:
        await test_a2a_communication(prompt)

    shutdown_servers(globals().get("a2a_server_processes", []))
    print("\n🛑 Shut down all A2A agent servers.")


if __name__ == "__main__":
    asyncio.run(main())
