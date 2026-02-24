<p align="center">
  <h1 align="center">Forge</h1>
  <p align="center"><strong>The universal AI agent runtime. Docker for agents.</strong></p>
  <p align="center">
    <a href="https://github.com/nautilus4707/Forge/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
    <img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python">
    <img src="https://img.shields.io/badge/version-0.1.0-green.svg" alt="Version">
  </p>
</p>

---

## What is Forge?

Forge is a runtime for building, running, and orchestrating AI agents. Define agents in YAML, run them from the CLI or Python, swap models with one line, and observe everything in a live dashboard. Think of it as Docker for AI agents.

## Features

- **Hot-swap models** — Switch between OpenAI, Anthropic, Google, Ollama, and more with a single line
- **Built-in tools** — Web search, URL fetch, file ops, shell, Python exec, HTTP requests out of the box
- **Memory** — SQLite + ChromaDB backends for persistent agent memory
- **Multi-agent orchestration** — Sequential, parallel, and supervisor workflows
- **Local-first** — Run 100% locally with Ollama. No API keys required
- **Observable** — REST API, WebSocket streaming, and live dashboard
- **Zero boilerplate** — Define agents in YAML or 5 lines of Python

## Quick Start

```bash
pip install -e .
forge init
forge run "What is the capital of France?"
```

## Define an Agent (YAML)

```yaml
agent:
  name: my-agent
  model: claude-sonnet-4-20250514
  # model: ollama/llama3.2:3b  # Free local alternative
  system_prompt: You are a helpful assistant.
  tools:
    - web_search
    - web_fetch
    - file_ops
    - python_exec
  cost_limit: 5.0
```

## Define an Agent (Python)

```python
from forge import Agent

agent = Agent(
    "my-agent",
    model="claude-sonnet-4-20250514",
    tools=["web_search", "file_ops"],
)
result = await agent.run("Research recent AI breakthroughs")
```

## Multi-Agent Workflows

```yaml
agents:
  - name: researcher
    model: claude-sonnet-4-20250514
    tools: [web_search, web_fetch]

  - name: writer
    model: ollama/llama3.2:3b
    tools: [file_ops]

workflows:
  - name: research-pipeline
    type: sequential
    steps:
      - agent: researcher
      - agent: writer
```

## Supported Models

| Provider | Models | Local |
|----------|--------|-------|
| **Anthropic** | Claude Sonnet, Haiku, Opus | No |
| **OpenAI** | GPT-4o, GPT-4o-mini, o1, o3-mini | No |
| **Google** | Gemini 2.0 Flash, Gemini 2.5 Pro | No |
| **Ollama** | Llama 3, Qwen, Phi, Mistral, etc. | Yes |
| **DeepSeek** | DeepSeek Chat, DeepSeek Reasoner | No |
| **Groq** | Llama 3.3 70B (fast inference) | No |
| **Together AI** | Any hosted model | No |
| **vLLM** | Any self-hosted model | Yes |

## Built-in Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search the web via DuckDuckGo |
| `web_fetch` | Fetch and extract text from URLs |
| `file_ops` | Read, write, list, delete files |
| `shell` | Execute shell commands |
| `python_exec` | Execute Python code |
| `http_request` | Make HTTP requests (GET/POST/PUT/DELETE) |

## CLI Reference

| Command | Description |
|---------|-------------|
| `forge run "prompt"` | Run an agent with a prompt |
| `forge init` | Create a template forgefile.yaml |
| `forge models` | List available models |
| `forge server` | Start the REST API server |
| `forge up` | Start agents from forgefile |

## API Server

```bash
forge server --port 8626
# API docs: http://localhost:8626/docs
```

Endpoints:
- `GET /health` — Health check
- `GET /api/v1/agents/` — List agents
- `POST /api/v1/agents/{name}/run` — Run an agent
- `GET /api/v1/tools/` — List tools
- `GET /api/v1/models/` — List models
- `WS /ws` — Real-time event stream

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[all,dev]"
pytest tests/ -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 — see [LICENSE](LICENSE).
