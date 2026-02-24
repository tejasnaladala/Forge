from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from forge.api.auth import require_api_key

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.get("/")
async def list_tools(request: Request, _key: str = Depends(require_api_key)):
    registry = request.app.state.tool_registry
    tools = []
    for name in registry.list_tools():
        tool = registry.get(name)
        tools.append({
            "name": tool.name,
            "description": tool.description,
        })
    return {"tools": tools}
