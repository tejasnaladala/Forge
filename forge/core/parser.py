from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template

from forge.core.types import AgentConfig, MemoryConfig, ModelConfig, ModelProvider, ToolConfig


PROVIDER_INFERENCE = {
    "gpt-": ModelProvider.OPENAI,
    "o1": ModelProvider.OPENAI,
    "o3": ModelProvider.OPENAI,
    "claude-": ModelProvider.ANTHROPIC,
    "gemini-": ModelProvider.GOOGLE,
    "llama": ModelProvider.OLLAMA,
    "qwen": ModelProvider.OLLAMA,
    "mistral": ModelProvider.OLLAMA,
    "phi-": ModelProvider.OLLAMA,
    "deepseek": ModelProvider.DEEPSEEK,
}


class ForgefileParser:
    def parse_file(self, path: str | Path) -> dict:
        path = Path(path)
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return self.parse_dict(raw or {})

    def parse_dict(self, raw_dict: dict) -> dict:
        result: dict[str, Any] = {"agents": {}, "workflows": [], "settings": {}}

        if "agent" in raw_dict:
            agent = self._parse_agent(raw_dict["agent"])
            result["agents"][agent.name] = agent
        elif "agents" in raw_dict:
            agents_data = raw_dict["agents"]
            if isinstance(agents_data, list):
                for agent_raw in agents_data:
                    agent = self._parse_agent(agent_raw)
                    result["agents"][agent.name] = agent
            elif isinstance(agents_data, dict):
                for name, agent_raw in agents_data.items():
                    if isinstance(agent_raw, dict):
                        agent_raw.setdefault("name", name)
                        agent = self._parse_agent(agent_raw)
                        result["agents"][agent.name] = agent

        if "workflows" in raw_dict:
            result["workflows"] = raw_dict["workflows"]
        elif "workflow" in raw_dict:
            result["workflows"] = [raw_dict["workflow"]]

        if "settings" in raw_dict:
            result["settings"] = raw_dict["settings"]

        return result

    def _parse_agent(self, raw: dict) -> AgentConfig:
        kwargs: dict[str, Any] = {
            "name": raw.get("name", "default"),
        }

        for field in ["description", "version", "max_iterations", "max_tool_calls_per_step",
                       "planning_enabled", "self_eval_enabled", "delegates", "supervisor",
                       "allowed_tools", "blocked_tools", "cost_limit", "rate_limit", "tags", "metadata"]:
            if field in raw:
                kwargs[field] = raw[field]

        # Parse model
        model_raw = raw.get("model", "claude-sonnet-4-20250514")
        if isinstance(model_raw, str):
            kwargs["model"] = self._parse_model_shorthand(model_raw)
        elif isinstance(model_raw, dict):
            if "provider" in model_raw:
                model_raw["provider"] = ModelProvider(model_raw["provider"])
            kwargs["model"] = ModelConfig(**model_raw)

        # Parse system_prompt
        prompt = raw.get("system_prompt", "")
        if isinstance(prompt, str):
            if prompt.startswith("file:"):
                prompt_path = Path(prompt[5:].strip())
                if prompt_path.is_file():
                    prompt = prompt_path.read_text(encoding="utf-8")
            if "{{" in prompt:
                prompt = Template(prompt).render()
        kwargs["system_prompt"] = prompt

        # Parse tools
        tools_raw = raw.get("tools", [])
        tools = []
        for t in tools_raw:
            if isinstance(t, str):
                tools.append(ToolConfig(name=t))
            elif isinstance(t, dict):
                tools.append(ToolConfig(**t))
        kwargs["tools"] = tools

        # Parse memory
        if "memory" in raw:
            mem_raw = raw["memory"]
            if isinstance(mem_raw, dict):
                kwargs["memory"] = MemoryConfig(**mem_raw)

        return AgentConfig(**kwargs)

    @staticmethod
    def _parse_model_shorthand(model_string: str) -> ModelConfig:
        if "/" in model_string:
            parts = model_string.split("/", 1)
            provider = ModelProvider(parts[0])
            model = parts[1]
            return ModelConfig(provider=provider, model=model)

        for prefix, provider in PROVIDER_INFERENCE.items():
            if model_string.startswith(prefix):
                return ModelConfig(provider=provider, model=model_string)

        return ModelConfig(provider=ModelProvider.OPENAI, model=model_string)
