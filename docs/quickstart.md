# Quickstart Guide

Get a Forge agent running in under five minutes.

---

## Install

```bash
pip install forge-ai
```

Or install from source with all optional providers:

```bash
git clone https://github.com/nautilus4707/Forge.git
cd Forge
pip install -e ".[all]"
```

Requires Python 3.11 or later.

---

## Setup API Key or Ollama

### Option A: Cloud Provider (Anthropic, OpenAI, Google, etc.)

Copy the example environment file and fill in at least one key:

```bash
cp .env.example .env
```

Edit `.env` and set your key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Other supported providers: OpenAI, Google AI, Groq, Together, DeepSeek.

### Option B: Free Local Models with Ollama

Install [Ollama](https://ollama.com), then pull a model:

```bash
ollama pull llama3.2:3b
```

No API key required. Set the model in your forgefile to `ollama/llama3.2:3b`.

---

## Create Your First Agent

Generate a starter `forgefile.yaml`:

```bash
forge init
```

This creates a `forgefile.yaml` in the current directory with a default agent configuration:

```yaml
agent:
  name: my-agent
  model: claude-sonnet-4-20250514
  # model: ollama/llama3.2:3b  # Uncomment for free local model
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

## Run It

Run your agent with a prompt:

```bash
forge run "Summarize the latest Python 3.13 release notes"
```

Override the model on the fly:

```bash
forge run -m ollama/llama3.2:3b "What is 2+2?"
```

You will see the agent think, call tools, and produce a final response, along with cost and token usage.

---

## Customize

Edit `forgefile.yaml` to tailor the agent to your needs:

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

Key options:
- **model** -- any LiteLLM-compatible model string (e.g. `claude-sonnet-4-20250514`, `gpt-4o`, `ollama/llama3.2:3b`)
- **tools** -- list of built-in tools to enable
- **cost_limit** -- maximum spend per session in USD
- **memory.backend** -- `sqlite` for persistent memory

---

## Add Tools

### Built-in Tools

Forge ships with these built-in tools:

| Tool | Description |
|------|-------------|
| `web_search` | Search the web via DuckDuckGo |
| `web_fetch` | Fetch and extract content from URLs |
| `file_ops` | Read, write, and list files |
| `python_exec` | Execute Python code in a sandbox |
| `shell` | Run shell commands |
| `http_request` | Make HTTP requests |

Enable them by name in `forgefile.yaml` under `tools`.

### Custom Tools

Create custom tools using the `@tool` decorator:

```python
from forge.sdk import Agent, tool

@tool
async def weather(city: str) -> str:
    """Get current weather for a city."""
    # Your implementation here
    return f"Weather in {city}: 72F and sunny"

agent = Agent(
    name="weather-bot",
    model="claude-sonnet-4-20250514",
    tools=["web_search", weather],
)
```

---

## Python SDK

Use the Python SDK for programmatic control:

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

    # Check cost
    print(f"Total cost: ${agent.cost:.4f}")

asyncio.run(main())
```

---

## Multi-Agent Workflows

Define multiple agents and orchestration in your forgefile:

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

Start all agents as a server:

```bash
forge up
```

Workflow types:
- **sequential** -- agents run one after another, output feeds into the next
- **parallel** -- agents run concurrently
- **supervisor** -- a supervisor agent delegates to workers

---

## Dashboard

Start the API server to access the web dashboard and REST API:

```bash
forge server --port 8626
```

Or with Docker Compose:

```bash
docker compose up
```

The server exposes:
- **REST API** at `http://localhost:8626`
- **API docs** at `http://localhost:8626/docs`

---

## Next Steps

- Read the full [README](../README.md) for architecture details
- See [CONTRIBUTING.md](../CONTRIBUTING.md) to add tools or providers
- Browse built-in tools in `forge/tools/builtin/`
- Explore the SDK in `forge/sdk/`
- Check available models: `forge models`
