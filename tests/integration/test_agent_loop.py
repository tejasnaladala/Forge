"""Integration tests: full agent loop and orchestration with a mocked model.

These tests wire together the real registry, executor, memory manager, runtime,
and orchestration engine. Only the network-bound model call
(``ModelRouter.complete``) is replaced so the tests run offline and fast.
"""
from unittest.mock import AsyncMock

import pytest

from forge.core.runtime import AgentRuntime
from forge.core.types import AgentConfig, MemoryConfig, ModelConfig, ModelProvider
from forge.memory.manager import MemoryManager
from forge.models.router import ModelRouter
from forge.orchestration.engine import OrchestrationEngine
from forge.sdk import Agent, tool
from forge.tools.executor import ToolExecutor
from forge.tools.registry import ToolRegistry


def _completion(content="", tool_calls=None, cost=0.001):
    return {
        "content": content,
        "tool_calls": tool_calls,
        "model": "test-model",
        "tokens_in": 8,
        "tokens_out": 12,
        "cost": cost,
    }


@pytest.mark.asyncio
async def test_full_loop_with_tool_call(monkeypatch, tmp_path):
    """think -> tool call -> think -> final response, end to end."""
    monkeypatch.chdir(tmp_path)  # keep the sqlite memory db inside tmp
    calls = {"n": 0}

    async def fake_complete(*, model_config, messages, tools=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return _completion(
                tool_calls=[{"id": "c1", "name": "double", "arguments": {"n": 21}}],
            )
        return _completion(content="The answer is 42.")

    monkeypatch.setattr(ModelRouter, "complete", AsyncMock(side_effect=fake_complete))

    @tool
    async def double(n: int) -> int:
        """Double a number."""
        return n * 2

    agent = Agent(
        "calculator",
        model="ollama/test",
        tools=[double],
        memory_backend="sqlite",
    )
    result = await agent.run("Double 21.")

    assert result == "The answer is 42."
    assert calls["n"] == 2  # one tool round trip, then the final answer
    assert agent.cost == pytest.approx(0.002)


@pytest.mark.asyncio
async def test_sequential_workflow_passes_output_forward(monkeypatch, tmp_path):
    """A two-step sequential workflow runs both agents through the engine."""
    monkeypatch.chdir(tmp_path)
    outputs = iter(["research notes", "final article"])

    async def fake_complete(*, model_config, messages, tools=None):
        return _completion(content=next(outputs))

    monkeypatch.setattr(ModelRouter, "complete", AsyncMock(side_effect=fake_complete))

    engine = OrchestrationEngine()
    for name in ("researcher", "writer"):
        config = AgentConfig(
            name=name,
            model=ModelConfig(provider=ModelProvider.OLLAMA, model="test"),
            system_prompt=f"You are the {name}.",
            memory=MemoryConfig(backend="sqlite"),
        )
        registry = ToolRegistry()
        registry.load_builtins()
        runtime = AgentRuntime(
            config=config,
            model_router=ModelRouter(),
            tool_executor=ToolExecutor(registry),
            memory_manager=MemoryManager(config.memory),
        )
        engine.register_runtime(name, runtime)

    workflow = {
        "type": "sequential",
        "steps": [{"agent": "researcher"}, {"agent": "writer"}],
    }
    result = await engine.run_workflow(workflow, "Write about Forge.")

    assert "final article" in str(result)
