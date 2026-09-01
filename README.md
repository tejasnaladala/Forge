# Forge

[![CI](https://github.com/tejasnaladala/Forge/actions/workflows/ci.yml/badge.svg)](https://github.com/tejasnaladala/Forge/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)

Forge is a Python runtime for agents defined in YAML or through an async SDK. It executes model/tool loops, stores session history, tracks tokens and cost, and serves agents through a CLI or FastAPI. Hosted models route through [LiteLLM](https://github.com/BerriAI/litellm); Ollama and vLLM use direct HTTP adapters.

The current implementation includes:

- Anthropic, OpenAI, Google, DeepSeek, Groq, and Together model routing
- local Ollama and vLLM endpoints
- default-deny tool authorization with four built-in tools
- SQLite session memory and an experimental Chroma integration
- sequential and parallel multi-agent execution
- FastAPI, WebSocket events, and a local Next.js dashboard

## Install and run

Forge is installed from source:

```bash
git clone https://github.com/tejasnaladala/Forge.git
cd Forge
python -m pip install -e ".[all]"
```

For a hosted model, copy `.env.example` to `.env`, set one provider key, and run:

```bash
forge run "Summarize the latest Python release notes"
```

For local inference:

```bash
ollama pull llama3.2:3b
forge run -m ollama/llama3.2:3b "Explain optimistic concurrency in five sentences"
```

Run `forge init` in a new project directory to generate this shape of configuration:

```yaml
agent:
  name: researcher
  model: claude-sonnet-4-20250514
  system_prompt: |
    Find primary sources, compare their claims, and cite each conclusion.
  tools:
    - web_search
    - web_fetch
    - file_ops
  cost_limit: 5.0
  max_iterations: 25
  memory:
    backend: sqlite
```

The `tools` list is the agent's complete authorization policy. An empty or missing list exposes no tools to the model and authorizes no tool execution.

## Python SDK

```python
import asyncio

from forge import Agent, tool


@tool
async def word_count(text: str) -> int:
    """Count whitespace-delimited words."""
    return len(text.split())


async def main() -> None:
    agent = Agent(
        "editor",
        model="gpt-4o",
        tools=[word_count],
        cost_limit=1.0,
    )
    print(await agent.run("Count the words in: Forge keeps tool access explicit."))


asyncio.run(main())
```

`Agent.run()` and `Agent.chat()` return final response text. `Agent.stream()` yields runtime steps as they complete. All three methods are asynchronous.

## Runtime

Each run follows the same path:

1. Parse an `AgentConfig` from YAML or construct one through the SDK.
2. Send the conversation and schemas for authorized tools to the selected model.
3. Execute requested tools through `ToolExecutor` and append their results to the conversation.
4. Continue until the model returns a final response or `max_iterations` is reached.
5. Store the completed response and emit session and step events.

The runtime checks `cost_limit` before each model call. A call already in progress can take the session above that value; Forge stops before the following call.

### Model routing

| Route | Providers |
|---|---|
| LiteLLM | Anthropic, OpenAI, Google, DeepSeek, Groq, Together |
| Direct local adapter | Ollama |
| OpenAI-compatible local adapter | vLLM |

A model can be changed in the forgefile or for one CLI run:

```yaml
model: claude-sonnet-4-20250514
# model: ollama/llama3.2:3b
```

Provider credentials and local model servers remain external requirements. Tool-call support also depends on the selected model.

### Memory

SQLite stores completed assistant responses by session and supplies recent responses on later turns. Setting `memory.backend` to `chroma` constructs a Chroma collection while retaining the SQLite record.

```yaml
memory:
  backend: chroma
  embedding_provider: ollama
  embedding_model: nomic-embed-text
```

The Chroma path requires a compatible embedding provider. With the pinned local dependencies, the collection initialized but the requested Ollama embedding function was unavailable. Semantic store and retrieval remain unverified, and memory backends do not have integration coverage in the current test suite.

## Tools

| Tool | Implemented behavior |
|---|---|
| `web_search` | DuckDuckGo text search with titles, URLs, and snippets |
| `web_fetch` | HTTP(S) fetch with text extraction and a response-length limit |
| `http_request` | GET, POST, PUT, DELETE, and PATCH with a bounded response body |
| `file_ops` | Read, write, list, delete, and existence checks under `./forge_workspace` |

Outbound HTTP tools reject private and reserved IP ranges and validate redirect targets. `file_ops` rejects absolute paths and resolved paths outside its workspace.

Host `shell` and `python_exec` tools are disabled in configuration, registration, and execution. Forge has no host-execution override. Model-controlled code needs an external disposable sandbox with its own filesystem, network, secret, and resource boundaries.

### Custom tools

`@tool` derives a JSON schema from an async function's signature and docstring. Decorated functions can be passed directly to the SDK, as in the `word_count` example above.

### Plugins

Plugin modules expose `register_tools(registry)` and can be loaded explicitly or through the `forge.plugins` entry-point group:

```toml
[project.entry-points."forge.plugins"]
my_tools = "my_package.forge_tools"
```

```python
registry.load_plugins(modules=["my_package.forge_tools"])
```

Plugin code runs in the Forge process and should be treated as trusted application code. Loading failures are logged and skipped during entry-point discovery.

## Multi-agent workflows

The orchestration engine implements two workflow strategies:

```yaml
agents:
  researcher:
    model: claude-sonnet-4-20250514
    tools: [web_search, web_fetch]
  writer:
    model: ollama/llama3.2:3b
    tools: [file_ops]

workflow:
  type: sequential
  steps:
    - agent: researcher
    - agent: writer
```

- `sequential` passes each agent's output to the next agent.
- `parallel` sends the same input to each agent and returns the collected outputs.

`ForgefileParser` parses workflow definitions, and `OrchestrationEngine.run_workflow()` executes them after runtimes are registered. `forge up` registers agents and starts the API server; it does not launch a workflow. Current `supervisor` handling invokes the named supervisor once. Worker delegation is not implemented.

## API and dashboard

```bash
forge server --port 8626
# or
docker compose up --build
```

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Health check |
| `/api/v1/agents/` | GET, POST | List or register agents |
| `/api/v1/agents/{name}/run` | POST | Run an agent in a new session |
| `/api/v1/sessions/{agent}/new` | POST | Create a chat session |
| `/api/v1/sessions/{agent}/{session}/message` | POST | Continue a session |
| `/api/v1/tools/` | GET | List registered tools |
| `/api/v1/models/` | GET | List configured or reachable models |
| `/ws` | WebSocket | Stream runtime events |

OpenAPI documentation is served at `http://localhost:8626/docs`. The dashboard runs at `http://localhost:3000`, lists registered agents, opens chat sessions, and displays runtime events.

The server binds to `127.0.0.1` by default. Setting `FORGE_API_KEY` enables API-key checks with `X-API-Key` or `Authorization: Bearer`; leaving it unset keeps local endpoints unauthenticated. The current dashboard client does not attach an API key and is intended for the unauthenticated local setup.

## Development

```bash
python -m pip install -e ".[all,dev]"
ruff check forge tests
mypy forge                  # advisory in CI
pytest tests -v --cov=forge

cd dashboard
npm ci
npm run build
```

At this revision, Pytest collects 70 tests covering configuration parsing, the runtime loop, cost and iteration stops, tool authorization and timeouts, disabled host execution, plugin loading, cost accounting, and two mocked integration workflows. Live provider calls, API routes, the dashboard in a browser, and memory backends are outside that suite.

CI runs Ruff, advisory Mypy, and Pytest on Python 3.11 and 3.12, then builds the dashboard with Node 20.

## Project layout

```text
forge/
  core/          runtime, parser, events, and shared types
  models/        provider routing and cost accounting
  tools/         registry, authorization, executor, and built-ins
  memory/        SQLite and Chroma backends
  orchestration/ sequential and parallel workflows
  plugins/       module and entry-point loading
  api/           FastAPI routes and WebSocket stream
  sdk/           Agent and @tool interfaces
dashboard/       Next.js local dashboard
examples/        YAML and Python examples
tests/           unit and integration tests
```

## License

Apache 2.0. See [LICENSE](LICENSE).
