from __future__ import annotations

import json
import time
import uuid
from typing import Any

import httpx
import structlog

from forge.config import settings
from forge.core.types import ModelConfig, ModelProvider
from forge.models.cost import CostTracker

logger = structlog.get_logger()

# Suppress LiteLLM verbose logging
try:
    import litellm
    litellm.suppress_debug_info = True
    litellm.set_verbose = False
except ImportError:
    litellm = None

LITELLM_PREFIX_MAP = {
    ModelProvider.OPENAI: "",
    ModelProvider.ANTHROPIC: "",
    ModelProvider.GOOGLE: "gemini/",
    ModelProvider.DEEPSEEK: "deepseek/",
    ModelProvider.GROQ: "groq/",
    ModelProvider.TOGETHER: "together_ai/",
}


class ModelRouter:
    def __init__(self) -> None:
        self.cost_tracker = CostTracker()
        self._client = httpx.AsyncClient(timeout=120.0)
        self._api_keys = self._load_api_keys()

    def _load_api_keys(self) -> dict[str, str]:
        """Load API keys from settings into a private map instead of os.environ."""
        key_map = {}
        if settings.openai_api_key:
            key_map["OPENAI_API_KEY"] = settings.openai_api_key
        if settings.anthropic_api_key:
            key_map["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        if settings.google_ai_api_key:
            key_map["GOOGLE_AI_API_KEY"] = settings.google_ai_api_key
            key_map["GEMINI_API_KEY"] = settings.google_ai_api_key
        if settings.deepseek_api_key:
            key_map["DEEPSEEK_API_KEY"] = settings.deepseek_api_key
        if settings.groq_api_key:
            key_map["GROQ_API_KEY"] = settings.groq_api_key
        if settings.together_api_key:
            key_map["TOGETHER_API_KEY"] = settings.together_api_key
            key_map["TOGETHERAI_API_KEY"] = settings.together_api_key
        return key_map

    def _get_api_key_for_provider(self, provider: ModelProvider) -> str | None:
        """Get the API key for a given provider from the private key map."""
        provider_key_map = {
            ModelProvider.OPENAI: "OPENAI_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            ModelProvider.GOOGLE: "GOOGLE_AI_API_KEY",
            ModelProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
            ModelProvider.GROQ: "GROQ_API_KEY",
            ModelProvider.TOGETHER: "TOGETHER_API_KEY",
        }
        env_var = provider_key_map.get(provider)
        if env_var:
            return self._api_keys.get(env_var)
        return None

    async def complete(
        self,
        model_config: ModelConfig,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        start = time.time()

        try:
            if model_config.provider == ModelProvider.OLLAMA:
                result = await self._complete_ollama(model_config, messages, tools)
            elif model_config.provider == ModelProvider.VLLM:
                result = await self._complete_vllm(model_config, messages, tools)
            else:
                result = await self._complete_litellm(model_config, messages, tools)
        except Exception as e:
            if model_config.fallback:
                logger.warning("model_fallback", primary=model_config.model, fallback=model_config.fallback, error=str(e))
                from forge.core.parser import ForgefileParser
                parsed_fallback = ForgefileParser._parse_model_shorthand(model_config.fallback)
                fallback_config = ModelConfig(
                    provider=parsed_fallback.provider,
                    model=parsed_fallback.model,
                    temperature=model_config.temperature,
                    max_tokens=model_config.max_tokens,
                )
                result = await self.complete(fallback_config, messages, tools, **kwargs)
                return result
            raise

        latency_ms = (time.time() - start) * 1000
        result["latency_ms"] = latency_ms

        self.cost_tracker.track(
            model=result.get("model", model_config.model),
            tokens_in=result.get("tokens_in", 0),
            tokens_out=result.get("tokens_out", 0),
            cost=result.get("cost", 0.0),
        )

        return result

    async def _complete_litellm(
        self,
        config: ModelConfig,
        messages: list[dict],
        tools: list[dict] | None,
    ) -> dict[str, Any]:
        if litellm is None:
            raise ImportError("litellm is not installed")

        prefix = LITELLM_PREFIX_MAP.get(config.provider, "")
        model_str = f"{prefix}{config.model}"

        kwargs: dict[str, Any] = {
            "model": model_str,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        # Pass API key directly instead of relying on os.environ
        api_key = config.api_key or self._get_api_key_for_provider(config.provider)
        if api_key:
            kwargs["api_key"] = api_key
        if config.base_url:
            kwargs["api_base"] = config.base_url
        if tools:
            kwargs["tools"] = tools

        response = await litellm.acompletion(**kwargs)

        content = response.choices[0].message.content or ""
        tool_calls_raw = response.choices[0].message.tool_calls
        tool_calls = None

        if tool_calls_raw:
            tool_calls = []
            for tc in tool_calls_raw:
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": args,
                })

        usage = response.usage
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0

        try:
            cost = litellm.completion_cost(completion_response=response)
        except Exception:
            cost = 0.0

        return {
            "content": content,
            "tool_calls": tool_calls,
            "model": config.model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
        }

    async def _complete_ollama(
        self,
        config: ModelConfig,
        messages: list[dict],
        tools: list[dict] | None,
    ) -> dict[str, Any]:
        host = config.base_url or settings.ollama_host
        url = f"{host}/api/chat"

        payload: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": config.temperature,
            },
        }
        if tools:
            payload["tools"] = tools

        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        message = data.get("message", {})
        content = message.get("content", "")

        tool_calls = None
        raw_tool_calls = message.get("tool_calls")
        if raw_tool_calls:
            tool_calls = []
            for tc in raw_tool_calls:
                func = tc.get("function", {})
                args = func.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                tool_calls.append({
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "name": func.get("name", ""),
                    "arguments": args,
                })

        tokens_in = data.get("prompt_eval_count", 0)
        tokens_out = data.get("eval_count", 0)

        return {
            "content": content,
            "tool_calls": tool_calls,
            "model": config.model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": 0.0,
        }

    async def _complete_vllm(
        self,
        config: ModelConfig,
        messages: list[dict],
        tools: list[dict] | None,
    ) -> dict[str, Any]:
        host = config.base_url or settings.vllm_host
        url = f"{host}/v1/chat/completions"

        payload: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if tools:
            payload["tools"] = tools

        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "") or ""

        tool_calls = None
        raw_tool_calls = message.get("tool_calls")
        if raw_tool_calls:
            tool_calls = []
            for tc in raw_tool_calls:
                func = tc.get("function", {})
                args = func.get("arguments", "{}")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                tool_calls.append({
                    "id": tc.get("id", f"call_{uuid.uuid4().hex[:8]}"),
                    "name": func.get("name", ""),
                    "arguments": args,
                })

        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)

        return {
            "content": content,
            "tool_calls": tool_calls,
            "model": config.model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": 0.0,
        }

    async def list_available_models(self) -> list[dict]:
        models = []

        # Check Ollama
        try:
            response = await self._client.get(f"{settings.ollama_host}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                for m in data.get("models", []):
                    models.append({"provider": "ollama", "model": m["name"], "local": True})
        except Exception:
            pass

        # Check vLLM
        try:
            response = await self._client.get(f"{settings.vllm_host}/v1/models", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                for m in data.get("data", []):
                    models.append({"provider": "vllm", "model": m["id"], "local": True})
        except Exception:
            pass

        # Cloud models with API keys
        if settings.anthropic_api_key:
            for m in ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001", "claude-opus-4-20250514"]:
                models.append({"provider": "anthropic", "model": m, "local": False})
        if settings.openai_api_key:
            for m in ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"]:
                models.append({"provider": "openai", "model": m, "local": False})
        if settings.google_ai_api_key:
            for m in ["gemini-2.0-flash", "gemini-2.5-pro"]:
                models.append({"provider": "google", "model": m, "local": False})
        if settings.groq_api_key:
            models.append({"provider": "groq", "model": "llama-3.3-70b-versatile", "local": False})
        if settings.together_api_key:
            models.append({"provider": "together", "model": "meta-llama/Llama-3-70b-chat-hf", "local": False})
        if settings.deepseek_api_key:
            for m in ["deepseek-chat", "deepseek-reasoner"]:
                models.append({"provider": "deepseek", "model": m, "local": False})

        return models
