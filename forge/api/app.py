from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from forge.api.security import RateLimiter
from forge.config import settings
from forge.core.registry import AgentRegistry
from forge.models.router import ModelRouter
from forge.orchestration.engine import OrchestrationEngine
from forge.tools.executor import ToolExecutor
from forge.tools.registry import ToolRegistry
from forge.version import __version__

_rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_rpm,
    window_seconds=60,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()

    if not hasattr(app.state, "model_router"):
        app.state.model_router = ModelRouter()

    if not hasattr(app.state, "tool_registry"):
        tool_registry = ToolRegistry()
        tool_registry.load_builtins()
        app.state.tool_registry = tool_registry
        app.state.tool_executor = ToolExecutor(tool_registry)

    if not hasattr(app.state, "orchestration"):
        app.state.orchestration = OrchestrationEngine()

    if not hasattr(app.state, "agent_registry"):
        app.state.agent_registry = AgentRegistry()

    yield

    # Cleanup
    if hasattr(app.state, "model_router") and hasattr(app.state.model_router, "_client"):
        await app.state.model_router._client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Forge",
        description="Universal AI agent runtime. Define, execute, and orchestrate agents across any model provider.",
        version=__version__,
        lifespan=lifespan,
    )

    # CORS: restricted to configured origins only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["X-API-Key", "Authorization", "Content-Type"],
    )

    # Rate-limiting and request-size middleware
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        # Enforce max request body size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": f"Request body too large. Maximum {settings.max_request_size} bytes."},
            )

        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        try:
            _rate_limiter.check(request)
        except Exception as exc:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": str(exc)},
            )

        return await call_next(request)

    from forge.api.routes import health, agents, sessions, tools, models
    from forge.api.ws import stream

    app.include_router(health.router)
    app.include_router(agents.router)
    app.include_router(sessions.router)
    app.include_router(tools.router)
    app.include_router(models.router)
    app.include_router(stream.router)

    return app
