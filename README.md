# Forge

**The Universal AI Agent Runtime**

Forge is a runtime for defining, executing, and orchestrating AI agents. Agents are declared in YAML, executed from the command line or programmatically via Python, and can target any supported model provider without code changes. All agent activity is observable through a REST API, WebSocket event stream, and live web dashboard.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/nautilus4707/Forge/blob/master/LICENSE)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Version](https://img.shields.io/badge/version-0.1.0-green.svg)

---

## Overview

Forge abstracts away the differences between model providers, offering a consistent interface for agent definition, tool integration, memory management, and multi-agent orchestration.

AI agent development often involves tight coupling between agent logic and a specific model provider. Forge addresses this by treating agents as portable configurations. A single change to the `model` field in an agent's configuration is sufficient to switch between cloud providers or local inference. Ollama is supported as a first-class option, enabling fully offline operation with no API keys required.

Forge is designed for developers and teams building AI-powered workflows who require provider flexibility, reproducible agent definitions, and operational visibility.

---

## Key Features

- **Provider-agnostic model routing** — Route requests to OpenAI, Anthropic, Google, Ollama, vLLM, DeepSeek, Groq, or Together AI through a unified interface powered by LiteLLM.
- **Built-in tool library** — Web search, URL fetching, file operations, shell execution, Python execution, and HTTP requests are included out of the box.
- **Persistent memory** — SQLite and ChromaDB backends provide persistent agent memory across sessions.
- **Multi-agent orchestration** — Sequential, parallel, and supervisor workflow patterns for composing agents into pipelines.
- **Local-first inference** — Run entirely offline using Ollama. No API keys required.
- **Observability** — REST API, WebSocket event streaming, and a real-time web dashboard for monitoring agent execution.
- **Declarative configuration** — Define agents in YAML or instantiate them in five lines of Python.

---

## Architecture

Forge is structured around the following core components:

| Component | Description |
|-----------|-------------|
| **Agent Runtime** | Manages the execution loop, tool dispatch, and conversation state for each agent. |
| **Model Router** | Routes completion requests to the configured provider through LiteLLM. |
| **Tool Registry** | Discovers and loads built-in and custom tools, exposing them to the agent as callable functions. |
| **Memory Backends** | Pluggable storage layer supporting SQLite (relational) and ChromaDB (vector). |
| **Orchestrator** | Coordinates multi-agent workflows using sequential, parallel, and supervisor strategies. |
| **API Server** | FastAPI-based HTTP server exposing agents, tools, and models via REST endpoints and WebSocket streaming. |
| **Dashboard** | Next.js web interface for real-time monitoring and agent interaction. |

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

Copy the example environment file and configure at least one provider API key, or use Ollama for local inference:

```bash
cp .env.example .env
```

Edit `.env` and provide the appropriate credentials. Refer to the [Configuration](#configuration) section for details.

---

## Quick Start

Initialize a default agent configuration and run a prompt:

```bash
forge init
forge run "What is the capital of France?"
```

The `init` command creates a `forgefile.yaml` in the current directory with a default agent configuration. The `run` command executes the configured agent with the specified prompt.

---

## Usage

### Command-Line Interface

| Command | Description |
|---------|-------------|
| `forge run "prompt"` | Execute an agent with the given prompt. |
| `forge init` | Generate a default `forgefile.yaml` in the current directory. |
| `forge models` | List available models across all configured providers. |
| `forge server` | Start the REST API server. |
| `forge up` | Start all agents defined in the forgefile and launch the API server. |

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

For multi-turn conversations, streaming, and advanced SDK usage, refer to the [Quickstart Guide](docs/quickstart.md).

---

## Configuration

Forge uses a `forgefile.yaml` file for agent and workflow configuration.

### Agent Configuration

| Parameter | Description |
|-----------|-------------|
| `model` | Any LiteLLM-compatible model identifier (e.g., `claude-sonnet-4-20250514`, `gpt-4o`, `ollama/llama3.2:3b`). |
| `tools` | List of built-in or custom tool names to enable. |
| `system_prompt` | The system-level instruction provided to the model. |
| `cost_limit` | Maximum spend per session in USD. |
| `memory.backend` | Persistent memory backend (`sqlite`). |
| `temperature` | Sampling temperature for model responses. |
| `max_iterations` | Maximum number of agent loop iterations per session. |

### Environment Variables

Environment variables are defined in `.env`. Refer to `.env.example` for the complete list of supported variables, including provider API keys and runtime settings.

---

## Model Providers

Forge routes all completion requests through LiteLLM, providing a unified interface across providers. Switching providers requires only a change to the `model` field in the agent configuration.

| Provider | Example Models | Local |
|----------|---------------|-------|
| Anthropic | Claude Sonnet, Haiku, Opus | No |
| OpenAI | GPT-4o, GPT-4o-mini, o1, o3-mini | No |
| Google AI | Gemini 2.0 Flash, Gemini 2.5 Pro | No |
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

The API server exposes the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check. |
| `/api/v1/agents/` | GET | List configured agents. |
| `/api/v1/agents/{name}/run` | POST | Execute an agent. |
| `/api/v1/tools/` | GET | List available tools. |
| `/api/v1/models/` | GET | List available models. |
| `/ws` | WebSocket | Real-time event stream. |

Interactive API documentation is available at `http://localhost:8626/docs` when the server is running.

### Dashboard

The web dashboard provides real-time visibility into agent execution. Deploy it alongside the API server using Docker Compose:

```bash
docker compose up
```

| Service | URL |
|---------|-----|
| API Server | `http://localhost:8626` |
| API Documentation | `http://localhost:8626/docs` |
| Dashboard | `http://localhost:3000` |

---

## Built-in Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search the web using DuckDuckGo. |
| `web_fetch` | Fetch and extract text content from a URL. |
| `file_ops` | Read, write, list, and delete files. |
| `shell` | Execute shell commands. |
| `python_exec` | Execute Python code in a sandboxed environment. |
| `http_request` | Send HTTP requests (GET, POST, PUT, DELETE). |

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

### Workflow Types

| Type | Behavior |
|------|----------|
| `sequential` | Agents execute in order. Each agent receives the output of the previous agent. |
| `parallel` | Agents execute concurrently. |
| `supervisor` | A supervisor agent delegates tasks to worker agents. |

---

## Extensibility

### Custom Tools

Define custom tools using the `@tool` decorator:

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

### Adding a Model Provider

1. Add the provider to the `ModelProvider` enum in `forge/core/types.py`.
2. Add routing logic in `forge/models/router.py`.
3. Add cost data in `forge/models/cost.py`.

### Memory Backends

Forge supports pluggable memory backends. The default backend is SQLite. ChromaDB is available for vector-based retrieval.

---

## Contributing

Refer to [CONTRIBUTING.md](CONTRIBUTING.md) for development setup instructions, coding standards, and the pull request process.

---

## Roadmap

- Additional tool integrations (database, messaging, cloud services)
- Enhanced multi-agent coordination patterns
- Plugin system for third-party tool distribution
- Improved observability and distributed tracing

---

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for the full license text.
