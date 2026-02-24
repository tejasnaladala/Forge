"""Tests for forge.core.runtime."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forge.core.runtime import AgentRuntime
from forge.core.types import AgentConfig, MemoryConfig, ModelConfig, ModelProvider, StepType


@pytest.fixture
def mock_router():
    router = AsyncMock()
    router.complete = AsyncMock(return_value={
        "content": "Hello! The answer is 4.",
        "tool_calls": None,
        "model": "test-model",
        "tokens_in": 10,
        "tokens_out": 20,
        "cost": 0.001,
    })
    return router


@pytest.fixture
def mock_executor():
    executor = MagicMock()
    executor.get_tool_schemas = MagicMock(return_value=[])
    executor.execute = AsyncMock(return_value="tool result")
    return executor


@pytest.fixture
def mock_memory():
    memory = AsyncMock()
    memory.retrieve = AsyncMock(return_value=[])
    memory.store = AsyncMock()
    return memory


@pytest.fixture
def config():
    return AgentConfig(
        name="test",
        model=ModelConfig(provider=ModelProvider.OLLAMA, model="test"),
        system_prompt="You are a test assistant.",
        memory=MemoryConfig(),
    )


@pytest.fixture
def runtime(config, mock_router, mock_executor, mock_memory):
    return AgentRuntime(
        config=config,
        model_router=mock_router,
        tool_executor=mock_executor,
        memory_manager=mock_memory,
    )


@pytest.mark.asyncio
async def test_create_session(runtime):
    session = await runtime.create_session()
    assert session.agent_name == "test"
    assert len(session.messages) == 1  # system prompt
    assert session.messages[0].role == "system"


@pytest.mark.asyncio
async def test_run_returns_response(runtime, mock_router):
    session = await runtime.create_session()
    response = await runtime.run(session.id, "What is 2+2?")
    assert response.content == "Hello! The answer is 4."
    assert response.role == "assistant"


@pytest.mark.asyncio
async def test_cost_limit_stops_execution(runtime, mock_router):
    runtime.config.cost_limit = 0.0  # Immediately over limit
    session = await runtime.create_session()
    session.total_cost = 1.0  # Already over
    response = await runtime.run(session.id, "test")
    assert "Cost limit" in response.content


@pytest.mark.asyncio
async def test_max_iterations(runtime, mock_router):
    # Make the model always return tool calls so it loops
    mock_router.complete = AsyncMock(return_value={
        "content": "",
        "tool_calls": [{"id": "1", "name": "test_tool", "arguments": {}}],
        "model": "test",
        "tokens_in": 10,
        "tokens_out": 10,
        "cost": 0.0,
    })
    runtime.config.max_iterations = 2
    session = await runtime.create_session()
    response = await runtime.run(session.id, "test")
    assert "Maximum iterations" in response.content
