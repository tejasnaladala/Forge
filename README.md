# Forge

A runtime for building, running, and orchestrating AI agents. Define agents declaratively in YAML, execute them from the command line or Python, swap model providers with a single configuration change, and observe all activity through a live dashboard.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/nautilus4707/Forge/blob/master/LICENSE)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Version](https://img.shields.io/badge/version-0.1.0-green.svg)

---

## Overview

Forge provides a unified runtime for AI agents. It abstracts away the differences between model providers, offering a consistent interface for agent definition, tool integration, memory management, and multi-agent orchestration.

The project addresses a common challenge in AI agent development: the tight coupling between agent logic and specific model providers. With Forge, agents are defined as portable configurations that can target any supported provider without code changes. Local inference via Ollama is supported as a first-class option, enabling fully offline operation with no API keys required.

Forge is designed for developers and teams building AI-powered workflows who need provider flexibility, reproducible agent definitions, and operational visibility.

---

## Key Features

- **Provider-agnostic model routing** -- Switch between OpenAI, Anthropic, Google, Ollama, and other providers with a single configuration change via LiteLLM.
- **Built-in tool library** -- Web search, URL fetching, file operations, shell execution, Python execution, and HTTP requests are available out of the box.
- **Persistent memory** -- SQLite and ChromaDB backends provide persistent agent memory across sessions.
- **Multi-agent orchestration** -- Sequential, parallel, and supervisor workflow patterns for composing agents into pipelines.
- **Local-first execution** -- Run entirely offline using Ollama with no API keys required.
- **Observability** -- REST API, WebSocket event streaming, and a live web dashboard for monitoring agent activity.
- **Declarative configuration** -- Define agents in YAML or instantiate them in five lines of Python.

---

## Architecture Overview

Forge is structured around the following core components:

- **Agent runtime** -- Manages the execution loop, tool dispatch, and conversation state for each agent.
- **Model router** -- Routes requests to the configured provider through LiteLLM, enabling transparent provider switching.
- **Tool registry** -- Discovers and loads built-in and custom tools, exposing them to the agent as callable functions.
- **Memory backends** -- Pluggable storage layer supporting SQLite (relational) and ChromaDB (vector) for agent memory.
- **Orchestrator** -- Coordinates multi-agent workflows with sequential, parallel, and supervisor execution strategies.
- **API server** -- FastAPI-based server exposing agents, tools, and models via REST endpoints and WebSocket streaming.
- **Dashboard** -- Next.js web interface for real-time monitoring and interaction.

---

## Installation

### Prerequisites

- Python 3.11 or later
- (Optional) [Ollama](https://ollama.com) for local model inference
- (Optional) Docker and Docker Compose for containerized deployment

### Install from Source

```bash
git clone https://github.com/nautilus4707/Forge.git
cd Forge
pip install -e ".[all]"
```

### Install with Development Dependencies

```bash
pip install -e ".[all,dev]"
```

### Configure Environment

Copy the example environment file and set at least one provider API key, or configure Ollama for local inference:

```bash
cp .env.example .env
```

Edit `.env` and provide the appropriate credentials. See the [Configuration](#configuration) section for details.

---

## Quick Start

Initialize a default agent configuration and run a prompt:

```bash
forge init
forge run "What is the capital of France?"
```

This creates a `forgefile.yaml` in the current directory with a default agent configuration, then executes the agent with the specified prompt.

---

## Usage

### CLI

| Command | Description |
|---------|-------------|
| `forge run "prompt"` | Execute an agent with the given prompt |
| `forge init` | Generate a template `forgefile.yaml` |
| `forge models` | List available models across all configured providers |
| `forge server` | Start the REST API server |
| `forge up` | Start agents defined in the forgefile |

### YAML Agent Definition

```yaml
agent:
  name: my-agent
  model: claude-sonnet-4-20250514
  # model: ollama/llama3.2:3b  # Local alternative
  system_prompt: You are a helpful assistant.
  tools:
    - web_search
    - web_fetch
    - file_ops
    - python_exec
  cost_limit: 5.0
```

### Python SDK

```python
from forge import Agent

agent = Agent(
    "my-agent",
    model="claude-sonnet-4-20250514",
    tools=["web_search", "file_ops"],
)
result = await agent.run("Research recent AI breakthroughs")
```

For detailed SDK usage including multi-turn conversations and streaming, see the [Quickstart Guide](docs/quickstart.md).

---

## Configuration

Forge uses a `forgefile.yaml` file for agent and workflow configuration. Key configuration options:

| Parameter | Description |
|-----------|-------------|
| `model` | Any LiteLLM-compatible model string (e.g., `claude-sonnet-4-20250514`, `gpt-4o`, `ollama/llama3.2:3b`) |
| `tools` | List of built-in or custom tools to enable for the agent |
| `cost_limit` | Maximum spend per session in USD |
| `memory.backend` | Storage backend for persistent memory (`sqlite`) |
| `temperature` | Sampling temperature for model responses |
| `max_iterations` | Maximum number of agent loop iterations |

Environment variables are configured in `.env`. See `.env.example` for all supported variables.

---

## Model Abstraction

Forge routes all model requests through LiteLLM, providing a unified interface across providers. Switching providers requires only a change to the `model` field in the agent configuration.

### Supported Providers

| Provider | Example Models | Local |
|----------|---------------|-------|
| Anthropic | Claude Sonnet, Haiku, Opus | No |
| OpenAI | GPT-4o, GPT-4o-mini, o1, o3-mini | No |
| Google | Gemini 2.0 Flash, Gemini 2.5 Pro | No |
| Ollama | Llama 3, Qwen, Phi, Mistral | Yes |
| DeepSeek | DeepSeek Chat, DeepSeek Reasoner | No |
| Groq | Llama 3.3 70B | No |
| Together AI | Any hosted model | No |
| vLLM | Any self-hosted model | Yes |

---

## Observability

### API Server

```bash
forge server --port 8626
```

The server exposes the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/agents/` | GET | List configured agents |
| `/api/v1/agents/{name}/run` | POST | Execute an agent |
| `/api/v1/tools/` | GET | List available tools |
| `/api/v1/models/` | GET | List available models |
| `/ws` | WebSocket | Real-time event stream |

API documentation is available at `http://localhost:8626/docs` when the server is running.

### Dashboard

The web dashboard provides real-time visibility into agent execution. Deploy it alongside the API server using Docker Compose:

```bash
docker compose up
```

The dashboard is accessible at `http://localhost:3000`. The API server runs on port `8626`.

---

## Built-in Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search the web via DuckDuckGo |
| `web_fetch` | Fetch and extract text content from URLs |
| `file_ops` | Read, write, list, and delete files |
| `shell` | Execute shell commands |
| `python_exec` | Execute Python code in a sandboxed environment |
| `http_request` | Make HTTP requests (GET, POST, PUT, DELETE) |

---

## Multi-Agent Workflows

Define multiple agents and orchestration strategies in the forgefile:

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

Supported workflow types:

| Type | Behavior |
|------|----------|
| `sequential` | Agents execute in order; each agent receives the output of the previous agent. |
| `parallel` | Agents execute concurrently. |
| `supervisor` | A supervisor agent delegates tasks to worker agents. |

---

## Extensibility

### Custom Tools

Create custom tools using the `@tool` decorator:

```python
from forge.sdk import Agent, tool

@tool
async def weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: 72F and sunny"

agent = Agent(
    name="weather-bot",
    model="claude-sonnet-4-20250514",
    tools=["web_search", weather],
)
```

### Adding a New Model Provider

1. Add the provider to the `ModelProvider` enum in `forge/core/types.py`.
2. Add routing logic in `forge/models/router.py`.
3. Add cost data in `forge/models/cost.py`.

### Memory Backends

Forge supports pluggable memory backends. The default backend is SQLite. ChromaDB is available for vector-based memory operations.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and the pull request process.

---

## Roadmap

- Additional tool integrations (database, messaging, cloud services)
- Enhanced multi-agent coordination patterns
- Plugin system for third-party tool distribution
- Improved observability and tracing

---

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for the full license text.
