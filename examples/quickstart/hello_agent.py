"""Quickstart: Run a simple Forge agent."""
import asyncio
from forge import Agent

async def main():
    # Option 1: Local model (free, requires Ollama)
    agent = Agent("hello", model="ollama/llama3.2:3b", system_prompt="You are a friendly assistant. Be brief.")

    # Option 2: Claude (requires ANTHROPIC_API_KEY in .env)
    # agent = Agent("hello", model="claude-sonnet-4-20250514", system_prompt="You are a friendly assistant. Be brief.")

    result = await agent.run("What is the meaning of life? Answer in one sentence.")
    print(f"Response: {result}")
    print(f"Cost: ${agent.cost:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
