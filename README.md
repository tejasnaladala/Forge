# Forge

A runtime for defining and running AI agents that aren't tied to one model provider. Write the agent once in YAML or a few lines of Python, then point it at GPT-4o, Claude, Gemini, or a local Ollama model by changing a single line.

![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Tests](https://img.shields.io/badge/tests-49%20passing-green.svg)

## Why this exists

Most agent code ends up welded to whichever SDK you started with. Swapping providers means rewriting the call sites, the tool schemas, the streaming handling, all of it. Forge keeps the agent definition separate from the provider: the `model` field is the only thing that changes when you move from a hosted API to a model running on your laptop.

```yaml
model: claude-sonnet-4-20250514     # hosted
model: ollama/llama3.2:3b           # local, no API key
```

Everything else (tools, memory, the agent loop, the cost ceiling) stays the same. Routing goes through [LiteLLM](https://github.com/BerriAI/litellm), so eight provider families work out of the box: Anthropic, OpenAI, Google, DeepSeek, Groq, Together, plus Ollama and vLLM for self-hosted inference.

## Demo

> _Placeholder: a short asciinema/GIF of `forge init`, `forge run`, and the live dashboard goes here once recorded._

```
$ forge run "What is the capital of France?"
THINK   The capital of France is Paris.
RESPOND Paris.

Cost: $0.0007 | Tokens: 142 | Steps: 2
```

## Quickstart

```bash
git clone https://github.com/tejasnaladala/Forge.git
cd Forge
pip install -e ".[all]"
```

Set one provider key, or skip keys entirely and use Ollama:

```bash
cp .env.example .env        # then edit .env, e.g. ANTHROPIC_API_KEY=...
# or: ollama pull llama3.2:3b   and use model: ollama/llama3.2:3b
```

Generate a default agent and run it:

```bash
forge init                  # writes forgefile.yaml
forge run "Summarize the latest Python release notes"
forge run -m ollama/llama3.2:3b "What is 2 + 2?"   # override the model per run
```

The same agent from Python:

```python
import asyncio
from forge import Agent

async def main():
    agent = Agent(
        "researcher",
        model="claude-sonnet-4-20250514",
        tools=["web_search", "file_ops"],
    )
    print(await agent.run("Find three recent papers on agent memory"))

asyncio.run(main())
```

`agent.run` is a coroutine, so it needs a running event loop. In scripts that means `asyncio.run(...)`; in a notebook or an existing async context you can `await` it directly.

## How it works

An agent runs a think/act loop: ask the model, run any tools it requested, feed the results back, repeat until the model answers or a limit is hit. The loop stops on a final response, on `max_iterations`, or when the session cost crosses `cost_limit` (so a runaway agent can't quietly burn your budget).

| Component | What it does |
|-----------|--------------|
| Runtime | Drives the per-agent loop, tool dispatch, conversation state, and cost tracking. |
| Model router | Sends completions to the configured provider through LiteLLM, with optional fallback. |
| Tool registry | Holds built-in and custom tools and hands the model their JSON schemas. |
| Memory | SQLite for session recall, optional ChromaDB for vector retrieval. |
| Orchestrator | Runs multi-agent workflows: sequential, parallel, or supervisor. |
| API + dashboard | FastAPI server with a WebSocket event stream, and a Next.js dashboard on top of it. |

### Built-in tools

`web_search` (DuckDuckGo), `web_fetch`, `file_ops`, `shell`, `python_exec`, and `http_request`. The `shell` and `python_exec` tools run with guardrails; `python_exec` blocks a set of dangerous patterns before executing in a sandbox.

### Custom tools

Any async function becomes a tool with the `@tool` decorator. The schema is derived from the type hints and docstring:

```python
from forge.sdk import Agent, tool

@tool
async def weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"{city}: 72F and sunny"

agent = Agent("weather-bot", model="gpt-4o", tools=["web_search", weather])
```

### Plugins

Third-party packages can ship tools by exposing a `register_tools(registry)` function and advertising it under the `forge.plugins` entry-point group:

```toml
[project.entry-points."forge.plugins"]
my_tools = "my_package.forge_tools"
```

Forge discovers them through `ToolRegistry.load_plugins()` (or `forge.plugins.PluginLoader`). A broken plugin is logged and skipped rather than taking down the host.

### Multi-agent workflows

```yaml
agents:
  researcher:
    model: claude-sonnet-4-20250514
    tools: [web_search, web_fetch]
  writer:
    model: ollama/llama3.2:3b
    tools: [file_ops]

workflow:
  type: sequential        # sequential | parallel | supervisor
  steps:
    - agent: researcher
    - agent: writer
```

In a `sequential` workflow each agent receives the previous agent's output; `parallel` fans out the same input; `supervisor` lets one agent delegate to workers. Start everything with `forge up`.

## API and dashboard

```bash
forge server --port 8626        # REST + WebSocket
docker compose up               # API + Next.js dashboard together
```

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/v1/agents/` | GET | List agents |
| `/api/v1/agents/{name}/run` | POST | Run an agent |
| `/api/v1/tools/` | GET | List tools |
| `/api/v1/models/` | GET | List models |
| `/ws` | WS | Live event stream |

Interactive docs live at `http://localhost:8626/docs`; the dashboard runs on `http://localhost:3000`.

## Security

The API is meant to be exposed, so it ships with API-key auth (constant-time comparison), CORS configured from an allowlist, per-client rate limiting, a request-size cap, and basic IP blocking. The `python_exec` and `file_ops` tools are scoped rather than open-ended.

## Project layout

```
forge/
  core/          runtime, parser, event bus, types
  models/        provider router + cost table
  tools/         registry, executor, built-in tools
  memory/        sqlite + chroma backends
  orchestration/ multi-agent workflows
  plugins/       third-party tool loading
  api/           FastAPI server, routes, websocket
  sdk/           Agent class + @tool decorator
dashboard/       Next.js monitoring UI
tests/           unit + integration suites
```

## Development

```bash
pip install -e ".[all,dev]"
ruff check forge/ tests/        # lint + import order
mypy forge/                     # type check (advisory)
pytest tests/ --cov=forge       # 49 tests, unit + integration
```

CI runs lint, type-check, and the test suite on Python 3.11 and 3.12, and builds the dashboard, on every push and pull request.

## License

Apache 2.0. See [LICENSE](LICENSE).
