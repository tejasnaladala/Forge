from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from forge.config import settings
from forge.core.registry import AgentRegistry
from forge.models.router import ModelRouter
from forge.orchestration.engine import OrchestrationEngine
from forge.tools.executor import ToolExecutor
from forge.tools.registry import ToolRegistry
from forge.version import __version__


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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from forge.api.routes import health, agents, sessions, tools, models
    from forge.api.ws import stream

    app.include_router(health.router)
    app.include_router(agents.router)
    app.include_router(sessions.router)
    app.include_router(tools.router)
    app.include_router(models.router)
    app.include_router(stream.router)

    return app
