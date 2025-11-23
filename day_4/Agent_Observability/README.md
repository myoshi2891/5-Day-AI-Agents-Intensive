# Agent Observability

This refactored project demonstrates how to monitor Google ADK agents with a modular layout. Each layer (logging, tools, agents, plugins, runner, and entry point) is isolated so you can reuse or swap components without rewriting the rest of the stack.

## Directory layout

```
Agent_Observability/
├── agent.py                     # Entry point
├── agent_observability/
│   ├── __init__.py              # Convenience exports
│   ├── agents.py                # Agent factory helpers
│   ├── config.py                # Constants and retry settings
│   ├── logging_utils.py         # Log cleanup + configuration
│   ├── plugins.py               # Custom observability plugin
│   ├── runner.py                # Runner + execution helpers
│   └── tools.py                 # Domain specific tools
└── requirements.txt
```

## Execution flow

1. **Logging setup (`logging_utils.configure_logging`)**
   - Deletes stale `logger.log`, `web.log`, and `tunnel.log` so every run starts clean.
   - Configures structured logging (filename/line/level/message) and routes debug logs to `logger.log`.

2. **Configuration (`config.py`)**
   - Centralizes shared constants such as the Gemini model name, retry policy, and default natural language query.
   - Exposes `RETRY_CONFIG` so both search and research agents stay in sync when the API policy changes.

3. **Domain tools (`tools.count_papers`)**
   - Validates that every search result is a string before counting it, raising a descriptive error when malformed data is passed in by the agent.
   - Keeps the business logic (counting returned papers) separated from orchestration.

4. **Agent factory (`agents.py`)**
   - `create_google_search_agent` wires Google Search into an ADK agent that returns raw search snippets.
   - `create_research_agent` receives that search agent via `AgentTool`, invokes it for candidate papers, and then uses the `count_papers` tool to report both the list and the total.

5. **Plugins (`plugins.CountInvocationPlugin`)**
   - Implements two callbacks to track how many agent/model invocations occur per run.
   - Logs the counters, adding lightweight telemetry beyond the standard ADK `LoggingPlugin` output.

6. **Runner (`runner.build_runner` and `run_observability_demo`)**
   - Assembles the agents and plugins into an `InMemoryRunner`, ensuring every execution automatically includes `LoggingPlugin` plus the custom counter plugin.
   - `run_observability_demo` prints a short status banner, executes `runner.run_debug`, and streams rich traces to stdout.

7. **Entry point (`agent.py`)**
   - Calls `configure_logging`, resolves the query (prioritizing CLI argument or the `AGENT_QUERY` env var, falling back to `DEFAULT_QUERY`), and awaits `run_observability_demo`.
   - Keeps top-level logic tiny so other scripts/tests can import `agent_observability` and reuse the same factories.

## Running the demo

From the repository root:

```bash
python day_4/Agent_Observability/agent.py
```

Optionally override the default research topic:

```bash
AGENT_QUERY="Find papers on constitutional AI" python day_4/Agent_Observability/agent.py
```

The command will log structured traces to `logger.log` while also echoing the plugin output in the terminal.
