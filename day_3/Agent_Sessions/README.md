# Agent Sessions

This package demonstrates **stateful** ADK agents, contrasting in-memory chats with database backed sessions.  
The default export wires a Gemini powered chatbot to a SQLite database so that conversations persist between ADK CLI restarts.  
Opt-in demos showcase how to swap in an in-memory service for lightweight testing.

## Directory Layout

- `agent.py` – Public entrypoint that defines `root_agent`, the `run_session` helper, and a persistent `DatabaseSessionService`.
- `config.py` – Shared Gemini model configuration and retry policy.
- `storage/`
  - `database.py` – Utilities for building the SQLite-backed session service plus a `inspect_db_events()` debugger.
- `demos/`
  - `inmemory.py` – Optional script for running the agent with `InMemorySessionService` (no persistence).
- `my_agent_data.db` – SQLite file created on demand by the persistent session service.
- `requirements.txt` – Notebook/CLI dependencies.
- `__init__.py` – Public API exports mirroring `agent.py` and the storage helpers.

## Usage

Start ADK Web against this folder (pass a DB URI if you want a shared location):

```bash
adk web --session_service_uri sqlite:///day_3/Agent_Sessions/my_agent_data.db ./day_3
```

For quick local tests without persistence:

```bash
python -m day_3.Agent_Sessions.demos.inmemory
```

To inspect the stored events directly:

```python
from day_3.Agent_Sessions.storage import inspect_db_events
inspect_db_events()
```
