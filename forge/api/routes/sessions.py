from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


class MessageRequest(BaseModel):
    message: str


@router.get("/{agent_name}")
async def list_sessions(request: Request, agent_name: str):
    runtime = request.app.state.orchestration.get_runtime(agent_name)
    if runtime is None:
        return {"error": f"Agent '{agent_name}' not found"}

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
async def create_session(request: Request, agent_name: str):
    runtime = request.app.state.orchestration.get_runtime(agent_name)
    if runtime is None:
        return {"error": f"Agent '{agent_name}' not found"}

    session = await runtime.create_session()
    return {"session_id": session.id, "agent": agent_name}


@router.post("/{agent_name}/{session_id}/message")
async def send_message(request: Request, agent_name: str, session_id: str, body: MessageRequest):
    runtime = request.app.state.orchestration.get_runtime(agent_name)
    if runtime is None:
        return {"error": f"Agent '{agent_name}' not found"}

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
        return {"error": str(e)}
