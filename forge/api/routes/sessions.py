from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from forge.api.auth import require_api_key

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

_VALID_NAME = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")
_VALID_SESSION_ID = re.compile(r"^[a-fA-F0-9\-]{1,64}$")


class MessageRequest(BaseModel):
    message: str = Field(max_length=100_000)


@router.get("/{agent_name}")
async def list_sessions(request: Request, agent_name: str, _key: str = Depends(require_api_key)):
    if not _VALID_NAME.match(agent_name):
        return JSONResponse(status_code=400, content={"error": "Invalid agent name."})

    runtime = request.app.state.orchestration.get_runtime(agent_name)
    if runtime is None:
        return JSONResponse(status_code=404, content={"error": f"Agent '{agent_name}' not found"})

    sessions = []
    for s in runtime.list_sessions():
        sessions.append({
            "id": s.id,
            "status": s.status.value,
            "total_cost": s.total_cost,
            "messages": len(s.messages),
            "created_at": s.created_at.isoformat(),
        })
    return {"sessions": sessions}


@router.post("/{agent_name}/new")
async def create_session(request: Request, agent_name: str, _key: str = Depends(require_api_key)):
    if not _VALID_NAME.match(agent_name):
        return JSONResponse(status_code=400, content={"error": "Invalid agent name."})

    runtime = request.app.state.orchestration.get_runtime(agent_name)
    if runtime is None:
        return JSONResponse(status_code=404, content={"error": f"Agent '{agent_name}' not found"})

    session = await runtime.create_session()
    return {"session_id": session.id, "agent": agent_name}


@router.post("/{agent_name}/{session_id}/message")
async def send_message(request: Request, agent_name: str, session_id: str, body: MessageRequest, _key: str = Depends(require_api_key)):
    if not _VALID_NAME.match(agent_name):
        return JSONResponse(status_code=400, content={"error": "Invalid agent name."})
    if not _VALID_SESSION_ID.match(session_id):
        return JSONResponse(status_code=400, content={"error": "Invalid session ID."})

    runtime = request.app.state.orchestration.get_runtime(agent_name)
    if runtime is None:
        return JSONResponse(status_code=404, content={"error": f"Agent '{agent_name}' not found"})

    try:
        response = await runtime.run(session_id, body.message, stream=False)
        session = runtime.get_session(session_id)
        return {
            "response": response.content or "",
            "session_id": session_id,
            "cost": session.total_cost if session else 0,
            "steps": len(session.steps) if session else 0,
        }
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
