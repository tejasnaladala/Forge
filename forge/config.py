from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class ForgeSettings(BaseSettings):
    model_config = {"env_prefix": "FORGE_", "env_file": ".env", "extra": "ignore"}

    host: str = "0.0.0.0"
    port: int = 8626
    debug: bool = False
    log_level: str = "INFO"

    home_dir: Path = Field(default_factory=lambda: Path.home() / ".forge")
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".forge" / "data")

    database_url: str = "sqlite+aiosqlite:///forge.db"
    default_provider: str = "anthropic"
    default_model: str = "claude-sonnet-4-20250514"

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_ai_api_key: str | None = None
    deepseek_api_key: str | None = None
    groq_api_key: str | None = None
    together_api_key: str | None = None

    ollama_host: str = "http://localhost:11434"
    vllm_host: str = "http://localhost:8000"
    chroma_host: str | None = None
    redis_url: str | None = None

    tracing_enabled: bool = True
    cost_tracking_enabled: bool = True
    max_concurrent_sessions: int = 50
    max_session_duration: int = 3600
    default_cost_limit: float = 10.0

    def model_post_init(self, __context: object) -> None:
        # Load API keys from env without FORGE_ prefix
        if self.anthropic_api_key is None:
            self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if self.openai_api_key is None:
            self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if self.google_ai_api_key is None:
            self.google_ai_api_key = os.environ.get("GOOGLE_AI_API_KEY")
        if self.deepseek_api_key is None:
            self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
        if self.groq_api_key is None:
            self.groq_api_key = os.environ.get("GROQ_API_KEY")
        if self.together_api_key is None:
            self.together_api_key = os.environ.get("TOGETHER_API_KEY")

    def ensure_dirs(self) -> None:
        self.home_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


settings = ForgeSettings()
