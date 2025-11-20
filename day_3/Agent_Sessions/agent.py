
import asyncio
from pathlib import Path

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.runners import Runner
from google.genai import types

from .config import DEFAULT_MODEL_NAME, retry_config

APP_NAME = "default"  # Application
USER_ID = "default"  # User

# --- Start of Change ---
# Use an absolute path for the database to avoid CWD issues.
# This ensures the DB file is always created next to this agent.py file.
_SCRIPT_DIR = Path(__file__).parent.resolve()
_DB_PATH = _SCRIPT_DIR / "my_agent_data.db"
DB_URL = f"sqlite:///{_DB_PATH}"
# --- End of Change ---

MODEL_NAME = DEFAULT_MODEL_NAME

print("✅ ADK components imported successfully.")

import sqlite3


def check_data_in_db() -> list[tuple]:
    """Inspect the underlying SQLite DB for debugging."""
    if not _DB_PATH.exists():
        print(f"-> Database file does not exist yet: {_DB_PATH}")
        return []

    try:
        with sqlite3.connect(_DB_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT app_name, session_id, author, content FROM events"
            )
            rows = cursor.fetchall()
            if not rows:
                print("-> No data found in 'events' table.")
            else:
                print("-> events columns: app_name, session_id, author, content")
                for each in rows:
                    print(each)
            return rows
    except sqlite3.OperationalError as e:
        print(f"-> Database error: {e}")
        print(
            "-> The 'events' table might not exist yet. Try running a session first."
        )
        return []


# Uncomment when you explicitly want to inspect the DB during development.
# check_data_in_db()

# Database-backed session service used by the exported runner
session_service: BaseSessionService = DatabaseSessionService(db_url=DB_URL)


# Define helper functions that will be reused throughout the notebook
async def run_session(
    runner_instance: Runner,
    user_queries: list[str] | str | None = None,
    session_name: str = "default",
    session_service_override: BaseSessionService | None = None,
):
    print(f"\n ### Session: {session_name}")

    # Get app name from the Runner
    app_name = runner_instance.app_name

    service = session_service_override or session_service

    # Attempt to create a new session or retrieve an existing one
    try:
        session = await service.create_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )
    except:
        session = await service.get_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )

    if session is None:
        raise RuntimeError("Session service returned no session instance.")

    # Process queries if provided
    if user_queries:
        # Convert single query to list for uniform processing
        if type(user_queries) == str:
            user_queries = [user_queries]

        # Process each query in the list sequentially
        for query in user_queries:
            print(f"\nUser > {query}")

            # Convert the query string to the ADK Content format
            query = types.Content(role="user", parts=[types.Part(text=query)])

            # Stream the agent's response asynchronously
            async for event in runner_instance.run_async(
                user_id=USER_ID, session_id=session.id, new_message=query
            ):
                # Check if the event contains valid content
                if event.content and event.content.parts:
                    # Filter out empty or "None" responses before printing
                    if (
                        event.content.parts[0].text != "None"
                        and event.content.parts[0].text
                    ):
                        print(f"{MODEL_NAME} > ", event.content.parts[0].text)
    else:
        print("No queries!")


print("✅ Helper functions defined.")

# Step 1: Create the LLM Agent
root_agent = Agent(
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    name="text_chat_bot",
    description="A text chatbot",  # Description of the agent's purpose
)

# Step 3: Create the Runner
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

print("✅ Stateful agent initialized!")
print(f"   - Application: {APP_NAME}")
print(f"   - User: {USER_ID}")
print(f"   - Using persistent DB: {DB_URL}")


async def _demo_stateful_session() -> None:
    """Fire a quick demo conversation when the module is executed directly."""
    await run_session(
        runner,
        [
            "Hi, I am Sam! What is the capital of United States?",
            "Hello! What is my name?",  # This time, the agent should remember!
        ],
        "test-db-session-01",
    )


if __name__ == "__main__":
    asyncio.run(_demo_stateful_session())
