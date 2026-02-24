"""Forge — The Universal AI Agent Runtime.

Usage:
    from forge import Agent
    agent = Agent("my-agent", model="claude-sonnet-4-20250514")
    result = await agent.run("Hello!")
"""
from __future__ import annotations

from forge.version import __version__
from forge.sdk.agent import Agent
from forge.sdk.decorators import tool, forge_tool
from forge.core.types import (
    AgentConfig,
    ModelConfig,
    ToolConfig,
    MemoryConfig,
    Session,
    Message,
    Step,
)

__all__ = [
    "__version__",
    "Agent",
    "tool",
    "forge_tool",
    "AgentConfig",
    "ModelConfig",
    "ToolConfig",
    "MemoryConfig",
    "Session",
    "Message",
    "Step",
]
