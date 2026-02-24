# Quickstart Guide

This guide covers installing Forge, configuring a model provider, defining an agent, and executing it.

---

## Prerequisites

- Python 3.11 or later
- (Optional) [Ollama](https://ollama.com) for local model inference

---

## Installation

### From Source

```bash
git clone https://github.com/nautilus4707/Forge.git
cd Forge
pip install -e ".[all]"
```

---

## Provider Configuration

Forge requires at least one configured model provider. Choose a cloud provider or use Ollama for local inference.

### Option A: Cloud Provider

Copy the example environment file and set the API key for your chosen provider:

```bash
cp .env.example .env
```

Edit `.env` and provide the appropriate key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Supported cloud providers: Anthropic, OpenAI, Google AI, Groq, Together AI, DeepSeek.

### Option B: Local Inference with Ollama

Install [Ollama](https://ollama.com) and pull a model:

```bash
ollama pull llama3.2:3b
```

No API key is required. Set the model field in your forgefile to `ollama/llama3.2:3b`.

---

## Defining an Agent

Generate a default `forgefile.yaml`:

```bash
forge init
```

This creates a configuration file in the current directory:

```yaml
agent:
  name: my-agent
  model: claude-sonnet-4-20250514
  # model: ollama/llama3.2:3b  # Uncomment for local inference
  system_prompt: |
    You are a helpful AI assistant. You can search the web,
    fetch URLs, read/write files, and execute code.
    Be concise and helpful.
  tools:
    - web_search
    - web_fetch
    - file_ops
    - python_exec
  cost_limit: 5.0
  memory:
    backend: sqlite
```

---

## Running an Agent

Execute the agent with a prompt:

```bash
forge run "Summarize the latest Python 3.13 release notes"
```

Override the model at runtime:

```bash
forge run -m ollama/llama3.2:3b "What is 2+2?"
```

The output includes the agent's reasoning steps, tool invocations, final response, and a cost and token usage summary.

---

## Agent Customization

Edit `forgefile.yaml` to configure the agent for a specific use case:

```yaml
agent:
  name: researcher
  model: gpt-4o
  system_prompt: |
    You are a research assistant. Find authoritative sources,
    cross-reference facts, and provide citations.
  tools:
    - web_search
    - web_fetch
    - file_ops
  cost_limit: 2.0
  memory:
    backend: sqlite
```

### Configuration Reference

| Parameter | Description |
|-----------|-------------|
| `model` | Any LiteLLM-compatible model identifier (e.g., `claude-sonnet-4-20250514`, `gpt-4o`, `ollama/llama3.2:3b`). |
| `tools` | List of built-in tool names to enable. |
| `system_prompt` | The system-level instruction provided to the model. |
| `cost_limit` | Maximum spend per session in USD. |
| `memory.backend` | Persistent memory backend (`sqlite`). |
| `temperature` | Sampling temperature for model responses. |
| `max_iterations` | Maximum number of agent loop iterations per session. |

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

Enable tools by name in the `tools` list within `forgefile.yaml`.

---

## Custom Tools

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

Custom tools are registered automatically when passed to the `Agent` constructor.

---

## Python SDK

The Python SDK provides programmatic access to all agent capabilities:

```python
import asyncio
from forge.sdk import Agent

async def main():
    agent = Agent(
        name="assistant",
        model="claude-sonnet-4-20250514",
        tools=["web_search", "file_ops"],
    )

    # Single response
    result = await agent.run("What are the top Python web frameworks?")
    print(result)

    # Multi-turn conversation
    await agent.chat("Tell me about FastAPI")
    await agent.chat("How does it compare to Django?")

    # Streaming
    async for step in agent.stream("Analyze this codebase"):
        print(step.type, step.output)

    # Cost tracking
    print(f"Total cost: ${agent.cost:.4f}")

asyncio.run(main())
```

---

## Multi-Agent Workflows

Define multiple agents and an orchestration strategy in the forgefile:

```yaml
agents:
  researcher:
    model: claude-sonnet-4-20250514
    system_prompt: "You find and summarize information."
    tools:
      - web_search
      - web_fetch

  writer:
    model: gpt-4o
    system_prompt: "You write polished content from research notes."
    tools:
      - file_ops

workflow:
  type: sequential
  steps:
    - agent: researcher
    - agent: writer
```

Start all agents and launch the API server:

```bash
forge up
```

### Workflow Types

| Type | Behavior |
|------|----------|
| `sequential` | Agents execute in order. Each agent receives the output of the previous agent. |
| `parallel` | Agents execute concurrently. |
| `supervisor` | A supervisor agent delegates tasks to worker agents. |

---

## API Server and Dashboard

Start the API server:

```bash
forge server --port 8626
```

Deploy with Docker Compose (includes the dashboard):

```bash
docker compose up
```

| Service | URL |
|---------|-----|
| API Server | `http://localhost:8626` |
| API Documentation | `http://localhost:8626/docs` |
| Dashboard | `http://localhost:3000` |

---

## Next Steps

- Review the [README](../README.md) for architecture details and the complete feature set.
- Refer to [CONTRIBUTING.md](../CONTRIBUTING.md) for instructions on adding tools or providers.
- Browse built-in tool implementations in `forge/tools/builtin/`.
- Explore the SDK source in `forge/sdk/`.
- List available models: `forge models`.
