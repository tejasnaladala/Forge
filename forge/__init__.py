"""Forge -- universal AI agent runtime.

Define, execute, and orchestrate AI agents across any model provider.

Usage::

    from forge import Agent
    agent = Agent("my-agent", model="claude-sonnet-4-20250514")
    result = await agent.run("Hello!")
"""
from __future__ import annotations

from forge.core.types import (
    AgentConfig,
    MemoryConfig,
    Message,
    ModelConfig,
    Session,
    Step,
    ToolConfig,
)
from forge.sdk.agent import Agent
from forge.sdk.decorators import forge_tool, tool
from forge.version import __version__

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
