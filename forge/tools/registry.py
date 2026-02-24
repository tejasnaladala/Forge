from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class RegisteredTool:
    name: str
    func: Callable
    description: str
    parameters: dict[str, Any]
    requires_approval: bool = False
    timeout: int = 30


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: dict[str, Any],
        requires_approval: bool = False,
        timeout: int = 30,
    ) -> None:
        self._tools[name] = RegisteredTool(
            name=name,
            func=func,
            description=description,
            parameters=parameters,
            requires_approval=requires_approval,
            timeout=timeout,
        )

    def get(self, name: str) -> RegisteredTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_schemas(
        self,
        allowed: list[str] | None = None,
        blocked: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        blocked = blocked or []
        schemas = []
        for name, tool in self._tools.items():
            if allowed is not None and name not in allowed:
                continue
            if name in blocked:
                continue
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )
        return schemas

    def load_builtins(self) -> None:
        from forge.tools.builtin import web_search, web_fetch, file_ops, shell, python_exec, http_request

        for module in [web_search, web_fetch, file_ops, shell, python_exec, http_request]:
            module.register_tools(self)
