from __future__ import annotations

from forge.core.types import AgentConfig


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentConfig] = {}

    def register(self, config: AgentConfig) -> None:
        self._agents[config.name] = config

    def get(self, name: str) -> AgentConfig | None:
        return self._agents.get(name)

    def list_all(self) -> list[AgentConfig]:
        return list(self._agents.values())

    def remove(self, name: str) -> bool:
        if name in self._agents:
            del self._agents[name]
            return True
        return False
