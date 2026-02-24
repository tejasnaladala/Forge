from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class StepType(str, Enum):
    THINK = "think"
    TOOL_CALL = "tool_call"
    OBSERVE = "observe"
    RESPOND = "respond"
    DELEGATE = "delegate"
    MEMORY = "memory"


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    VLLM = "vllm"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    TOGETHER = "together"
    CUSTOM = "custom"


class MemoryType(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class ModelConfig(BaseModel):
    provider: ModelProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    api_key: str | None = None
    base_url: str | None = None
    fallback: str | None = None
    cost_limit: float | None = None
    rate_limit: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ToolConfig(BaseModel):
    name: str
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    returns: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    timeout: int = 30
    sandbox: bool = False
    enabled: bool = True


class MemoryConfig(BaseModel):
    backend: str = "sqlite"
    embedding_model: str = "nomic-embed-text"
    embedding_provider: str = "ollama"
    max_working_memory: int = 50
    semantic_search_k: int = 5
    persist_path: str = ".forge/memory"


class AgentConfig(BaseModel):
    name: str
    description: str = ""
    version: str = "0.1.0"
    system_prompt: str = ""
    model: ModelConfig = Field(
        default_factory=lambda: ModelConfig(provider=ModelProvider.ANTHROPIC, model="claude-sonnet-4-20250514")
    )
    tools: list[ToolConfig] = Field(default_factory=list)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    max_iterations: int = 25
    max_tool_calls_per_step: int = 5
    planning_enabled: bool = True
    self_eval_enabled: bool = False
    delegates: list[str] = Field(default_factory=list)
    supervisor: str | None = None
    allowed_tools: list[str] | None = None
    blocked_tools: list[str] = Field(default_factory=list)
    cost_limit: float = 10.0
    rate_limit: int = 60
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    role: str  # system, user, assistant, tool
    content: str | None = None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    result: Any = None
    error: str | None = None
    duration_ms: float = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class Step(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: StepType
    input: Any = None
    output: Any = None
    model_used: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    duration_ms: float = 0
    error: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    status: AgentStatus = AgentStatus.IDLE
    messages: list[Message] = Field(default_factory=list)
    steps: list[Step] = Field(default_factory=list)
    total_cost: float = 0.0
    total_tokens: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ForgeEvent(BaseModel):
    type: str
    session_id: str = ""
    agent_name: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
