"""Tests for forge.core.types."""
import pytest
from forge.core.types import (
    AgentConfig, AgentStatus, MemoryConfig, Message, ModelConfig, ModelProvider,
    Session, Step, StepType, ToolCall, ToolConfig, ToolResult, ForgeEvent,
)


def test_model_config_defaults():
    config = ModelConfig(provider=ModelProvider.ANTHROPIC, model="claude-sonnet-4-20250514")
    assert config.temperature == 0.7
    assert config.max_tokens == 4096
    assert config.top_p == 1.0
    assert config.api_key is None


def test_agent_config_minimal():
    config = AgentConfig(name="test")
    assert config.name == "test"
    assert config.max_iterations == 25
    assert config.cost_limit == 10.0
    assert config.model.provider == ModelProvider.ANTHROPIC


def test_agent_config_with_model():
    config = AgentConfig(
        name="test",
        model=ModelConfig(provider=ModelProvider.OLLAMA, model="llama3.2:3b"),
        system_prompt="Hello",
    )
    assert config.model.provider == ModelProvider.OLLAMA
    assert config.model.model == "llama3.2:3b"


def test_session_defaults():
    session = Session(agent_name="test")
    assert session.status == AgentStatus.IDLE
    assert session.total_cost == 0.0
    assert len(session.messages) == 0
    assert session.id  # UUID generated


def test_session_status_change():
    session = Session(agent_name="test")
    session.status = AgentStatus.RUNNING
    assert session.status == AgentStatus.RUNNING


def test_step_with_metadata():
    step = Step(type=StepType.THINK, output="thinking...", metadata={"key": "value"})
    assert step.type == StepType.THINK
    assert step.output == "thinking..."
    assert step.metadata == {"key": "value"}
    assert step.id  # UUID generated


def test_message_creation():
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"
    assert msg.timestamp is not None


def test_tool_call():
    tc = ToolCall(name="web_search", arguments={"query": "test"})
    assert tc.name == "web_search"
    assert tc.id  # UUID generated


def test_tool_result():
    tr = ToolResult(tool_call_id="123", name="web_search", result=[{"title": "Test"}])
    assert tr.tool_call_id == "123"
    assert tr.duration_ms == 0


def test_tool_config_defaults():
    tc = ToolConfig(name="my_tool")
    assert tc.requires_approval is False
    assert tc.timeout == 30
    assert tc.enabled is True


def test_memory_config_defaults():
    mc = MemoryConfig()
    assert mc.backend == "sqlite"
    assert mc.embedding_model == "nomic-embed-text"


def test_forge_event():
    event = ForgeEvent(type="test.event", session_id="s1", agent_name="a1")
    assert event.type == "test.event"
    assert event.timestamp is not None


def test_model_provider_values():
    assert ModelProvider.OPENAI.value == "openai"
    assert ModelProvider.OLLAMA.value == "ollama"
    assert ModelProvider.ANTHROPIC.value == "anthropic"
