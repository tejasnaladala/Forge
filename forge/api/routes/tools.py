from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.get("/")
async def list_tools(request: Request):
    registry = request.app.state.tool_registry
    tools = []
    for name in registry.list_tools():
        tool = registry.get(name)
        tools.append({
            "name": tool.name,
            "description": tool.description,
        })
    return {"tools": tools}
