"""Run the research agent with streaming output."""
import asyncio
from forge import Agent
from forge.core.types import StepType

async def main():
    agent = Agent(
        "researcher",
        model="claude-sonnet-4-20250514",
        tools=["web_search", "web_fetch", "file_ops"],
        system_prompt="You are a research analyst. Search the web, read sources, and write a structured report.",
        temperature=0.3,
        cost_limit=5.0,
    )

    async for step in agent.stream("Research the latest developments in AI agents in 2025"):
        if step.type == StepType.THINK:
            print(f"[Think] {str(step.output)[:100]}")
        elif step.type == StepType.TOOL_CALL:
            tool_info = step.input or {}
            print(f"[Tool] {tool_info.get('tool', '?')}")
        elif step.type == StepType.RESPOND:
            print(f"\n{step.output}")

    print(f"\nTotal cost: ${agent.cost:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
