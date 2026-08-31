from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from forge.exceptions import ToolDisabledError
from forge.tools.policy import (
    DISABLED_HOST_EXECUTION_TOOLS,
    host_execution_disabled_message,
    normalize_authorized_tools,
)


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
        if name in DISABLED_HOST_EXECUTION_TOOLS:
            raise ToolDisabledError(host_execution_disabled_message(name))

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
        authorized: list[str] | set[str] | frozenset[str] | None = None,
    ) -> list[dict[str, Any]]:
        authorized_names = normalize_authorized_tools(authorized)
        schemas = []
        for name, tool in self._tools.items():
            if name in DISABLED_HOST_EXECUTION_TOOLS or name not in authorized_names:
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
        from forge.tools.builtin import (
            file_ops,
            http_request,
            web_fetch,
            web_search,
        )

        for module in [web_search, web_fetch, file_ops, http_request]:
            module.register_tools(self)

    def load_plugins(self, modules: list[str] | None = None, *, entry_points: bool = True) -> list[str]:
        """Load third-party tool plugins into this registry.

        Args:
            modules: Explicit dotted module paths to load. Each must expose a
                ``register_tools(registry)`` function.
            entry_points: When True, also load plugins advertised under the
                ``forge.plugins`` entry-point group.

        Returns:
            The names of tools added by the loaded plugins.
        """
        from forge.plugins.loader import PluginLoader

        loader = PluginLoader(self)
        for module_path in modules or []:
            loader.load_module(module_path)
        if entry_points:
            loader.load_entry_points()

        return [name for plugin in loader.loaded for name in plugin.tools]
