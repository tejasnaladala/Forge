"""Run the coding agent."""

import asyncio

from forge import Agent
from forge.core.types import StepType


async def main():
    agent = Agent(
        "coder",
        model="ollama/qwen2.5-coder:7b",
        tools=["file_ops"],
        system_prompt=(
            "You are an expert Python developer. Draft code and save the proposed files. "
            "Do not claim the code was executed or validated."
        ),
        temperature=0.2,
        max_iterations=30,
    )

    request = (
        "Write a Python function that finds all prime numbers up to N using the "
        "Sieve of Eratosthenes. Test it with N=100."
    )
    async for step in agent.stream(request):
        if step.type == StepType.TOOL_CALL:
            tool_info = step.input or {}
            print(f"[{tool_info.get('tool', '?')}]", end=" ")
        elif step.type == StepType.RESPOND:
            print(f"\n{step.output}")


if __name__ == "__main__":
    asyncio.run(main())
