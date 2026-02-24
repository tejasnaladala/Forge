from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from forge.api.auth import require_ws_api_key
from forge.core.events import event_bus
from forge.core.types import ForgeEvent

router = APIRouter()

_connections: list[WebSocket] = []
_broadcast_registered = False


async def _broadcast(event: ForgeEvent) -> None:
    data = json.dumps({
        "type": event.type,
        "session_id": event.session_id,
        "agent_name": event.agent_name,
        "data": event.data,
        "timestamp": event.timestamp.isoformat(),
    })
    disconnected = []
    for ws in _connections:
        try:
            await ws.send_text(data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in _connections:
            _connections.remove(ws)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global _broadcast_registered

    # Authenticate before accepting the connection
    try:
        await require_ws_api_key(websocket)
    except Exception:
        return

    await websocket.accept()
    _connections.append(websocket)

    if not _broadcast_registered:
        event_bus.on_all(_broadcast)
        _broadcast_registered = True

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _connections:
            _connections.remove(websocket)
