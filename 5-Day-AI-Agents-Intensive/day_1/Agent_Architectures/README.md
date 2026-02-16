# Agent Architectures

This package demonstrates several multi-agent workflows built with **google-adk**. The code only uses official ADK components and the Google Search tool—no custom network access, file writes, or secret handling—so there are no obvious security concerns under normal usage.

## Directory Layout

- `agent.py` – Public entrypoint that exposes the shared configuration helpers and the workflow builders/runners. It also defines `root_agent`, a router agent that inspects each prompt and launches the matching workflow.
- `config.py` – Centralized Gemini retry policy (`retry_config`) plus `build_model()` so every agent shares the same model configuration.
- `workflows/`
  - `research.py` – Research + summarization coordinator (`ResearchCoordinator`).
  - `blog_pipeline.py` – Outline → draft → edit sequential agent pipeline.
  - `executive_briefing.py` – Parallel research (tech, health, finance) followed by an aggregator producing an executive summary.
  - `story_refinement.py` – Writer → critic → refiner loop with the `exit_loop` function exposed as a `FunctionTool`.
  - `router.py` – Router agent that decides which workflow to run and explains its choice to the user.
  - `__init__.py` – Convenience exports for all builders/runners.
- `requirements.txt` – Python dependencies for the ADK demos.
- `__init__.py` – Package exports mirroring `agent.py`.

## Usage

Run the ADK CLI pointing at `day_1/Agent_Architectures` and issue prompts:

```bash
adk web day_1
```

- General research questions trigger the research workflow.
- Blog/article prompts trigger the blog pipeline.
- Requests mentioning “daily executive briefing” or tech/health/finance trends trigger the executive briefing pipeline.
- Creative writing/story prompts trigger the story refinement loop.
