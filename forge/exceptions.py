from __future__ import annotations


class ForgeError(Exception):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigError(ForgeError):
    pass


class AgentError(ForgeError):
    pass


class ModelError(ForgeError):
    pass


class ModelNotFoundError(ModelError):
    pass


class RateLimitError(ModelError):
    pass


class CostLimitError(ModelError):
    pass


class ToolError(ForgeError):
    pass


class ToolNotFoundError(ToolError):
    pass


class ToolTimeoutError(ToolError):
    pass


class MemoryError(ForgeError):
    pass


class ParserError(ForgeError):
    pass


class SessionError(ForgeError):
    pass
