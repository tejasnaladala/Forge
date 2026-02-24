from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from forge.api.auth import require_api_key
from forge.core.parser import ForgefileParser
from forge.core.runtime import AgentRuntime
from forge.core.types import AgentConfig, MemoryConfig, StepType
from forge.memory.manager import MemoryManager
from forge.tools.executor import ToolExecutor

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

_VALID_NAME = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


class CreateAgentRequest(BaseModel):
    config: dict


class RunAgentRequest(BaseModel):
    input: str = Field(max_length=100_000)


@router.get("/")
async def list_agents(request: Request, _key: str = Depends(require_api_key)):
    registry = request.app.state.agent_registry
    agents = []
    for config in registry.list_all():
        agents.append({
            "name": config.name,
            "description": config.description,
            "model": f"{config.model.provider.value}/{config.model.model}",
            "tools": [t.name for t in config.tools],
        })
    return {"agents": agents}


@router.post("/")
async def create_agent(request: Request, body: CreateAgentRequest, _key: str = Depends(require_api_key)):
    parser = ForgefileParser()
    config = parser._parse_agent(body.config)

    registry = request.app.state.agent_registry
    registry.register(config)

    tool_executor = request.app.state.tool_executor
    model_router = request.app.state.model_router
    memory_manager = MemoryManager(config.memory)

    runtime = AgentRuntime(
        config=config,
        model_router=model_router,
        tool_executor=tool_executor,
        memory_manager=memory_manager,
    )
    request.app.state.orchestration.register_runtime(config.name, runtime)

    return {"status": "created", "agent": config.name}


@router.get("/{name}")
async def get_agent(request: Request, name: str, _key: str = Depends(require_api_key)):
    if not _VALID_NAME.match(name):
        return JSONResponse(status_code=400, content={"error": "Invalid agent name."})

    registry = request.app.state.agent_registry
    config = registry.get(name)
    if config is None:
        return JSONResponse(status_code=404, content={"error": f"Agent '{name}' not found"})

    runtime = request.app.state.orchestration.get_runtime(name)
    session_count = len(runtime.list_sessions()) if runtime else 0

    return {
        "name": config.name,
        "description": config.description,
        "model": f"{config.model.provider.value}/{config.model.model}",
        "tools": [t.name for t in config.tools],
        "sessions": session_count,
    }


@router.post("/{name}/run")
async def run_agent(request: Request, name: str, body: RunAgentRequest, _key: str = Depends(require_api_key)):
    if not _VALID_NAME.match(name):
        return JSONResponse(status_code=400, content={"error": "Invalid agent name."})

    orchestration = request.app.state.orchestration
    try:
        result = await orchestration.run_agent(name, body.input)
        return result
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
