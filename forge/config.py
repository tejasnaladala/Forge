from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class ForgeSettings(BaseSettings):
    model_config = {"env_prefix": "FORGE_", "env_file": ".env", "extra": "ignore"}

    # Server -- default to localhost to avoid exposing on all interfaces
    host: str = "127.0.0.1"
    port: int = 8626
    debug: bool = False
    log_level: str = "INFO"

    # Security
    api_key: str | None = None
    cors_origins: str = "http://localhost:3000"
    rate_limit_rpm: int = 60
    max_request_size: int = 102400  # 100 KB

    # Directories
    home_dir: Path = Field(default_factory=lambda: Path.home() / ".forge")
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".forge" / "data")

    # Database
    database_url: str = "sqlite+aiosqlite:///forge.db"
    default_provider: str = "anthropic"
    default_model: str = "claude-sonnet-4-20250514"

    # LLM API keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_ai_api_key: str | None = None
    deepseek_api_key: str | None = None
    groq_api_key: str | None = None
    together_api_key: str | None = None

    # Infrastructure
    ollama_host: str = "http://localhost:11434"
    vllm_host: str = "http://localhost:8000"
    chroma_host: str | None = None
    redis_url: str | None = None

    # Observability
    tracing_enabled: bool = True
    cost_tracking_enabled: bool = True
    max_concurrent_sessions: int = 50
    max_session_duration: int = 3600
    default_cost_limit: float = 10.0

    # Tool security
    sandbox_shell: bool = True
    sandbox_python: bool = True
    allowed_shell_commands: str = "ls,cat,head,tail,grep,find,wc,echo,pwd,date,whoami,curl,wget,git,python,pip,node,npm"

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
        if self.api_key is None:
            self.api_key = os.environ.get("FORGE_API_KEY")

    def ensure_dirs(self) -> None:
        self.home_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def get_allowed_shell_commands(self) -> set[str]:
        """Parse comma-separated allowed shell commands into a set."""
        return {c.strip() for c in self.allowed_shell_commands.split(",") if c.strip()}


settings = ForgeSettings()
