from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from forge.core.parser import ForgefileParser
from forge.core.runtime import AgentRuntime
from forge.core.types import AgentConfig, MemoryConfig, ModelConfig, Session, Step, ToolConfig
from forge.memory.manager import MemoryManager
from forge.models.router import ModelRouter
from forge.tools.executor import ToolExecutor
from forge.tools.registry import ToolRegistry


class Agent:
    def __init__(
        self,
        name: str,
        model: str = "claude-sonnet-4-20250514",
        tools: list | None = None,
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        max_iterations: int = 25,
        cost_limit: float = 10.0,
        memory_backend: str = "sqlite",
        **kwargs,
    ) -> None:
        model_config = ForgefileParser._parse_model_shorthand(model)
        model_config.temperature = temperature
        model_config.max_tokens = max_tokens

        tool_registry = ToolRegistry()
        tool_registry.load_builtins()

        builtin_tool_names: list[str] = []
        custom_tools: list = []

        for t in (tools or []):
            if isinstance(t, str):
                builtin_tool_names.append(t)
            elif callable(t):
                custom_tools.append(t)

        # Register custom tools
        for func in custom_tools:
            if hasattr(func, "_forge_tool") and func._forge_tool:
                tool_registry.register(
                    name=func._forge_tool_name,
                    func=func,
                    description=func._forge_tool_description,
                    parameters=func._forge_tool_schema,
                )

        tool_configs = [ToolConfig(name=n) for n in builtin_tool_names]

        config = AgentConfig(
            name=name,
            system_prompt=system_prompt,
            model=model_config,
            tools=tool_configs,
            max_iterations=max_iterations,
            cost_limit=cost_limit,
            memory=MemoryConfig(backend=memory_backend),
            allowed_tools=builtin_tool_names + [f._forge_tool_name for f in custom_tools if hasattr(f, "_forge_tool_name")] or None,
            **kwargs,
        )

        self._model_router = ModelRouter()
        self._tool_executor = ToolExecutor(tool_registry)
        self._memory_manager = MemoryManager(config.memory)

        self._runtime = AgentRuntime(
            config=config,
            model_router=self._model_router,
            tool_executor=self._tool_executor,
            memory_manager=self._memory_manager,
        )

        self._session: Session | None = None
        self._config = config

    async def run(self, input_text: str) -> str:
        session = await self._runtime.create_session()
        self._session = session
        response = await self._runtime.run(session.id, input_text, stream=False)
        return response.content or ""

    async def stream(self, input_text: str) -> AsyncIterator[Step]:
        session = await self._runtime.create_session()
        self._session = session
        gen = await self._runtime.run(session.id, input_text, stream=True)
        async for step in gen:
            yield step

    async def chat(self, message: str) -> str:
        if self._session is None:
            self._session = await self._runtime.create_session()

        response = await self._runtime.run(self._session.id, message, stream=False)
        return response.content or ""

    @property
    def session(self) -> Session | None:
        return self._session

    @property
    def cost(self) -> float:
        if self._session:
            return self._session.total_cost
        return 0.0
