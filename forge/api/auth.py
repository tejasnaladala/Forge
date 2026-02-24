from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, WebSocket, status
from fastapi.security import APIKeyHeader

from forge.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())


async def require_api_key(
    request: Request,
    api_key: Optional[str] = Depends(_api_key_header),
) -> str:
    """FastAPI dependency that enforces API key authentication on routes.

    When FORGE_API_KEY is not set, authentication is disabled (local dev mode).
    """
    configured_key = settings.api_key
    if not configured_key:
        return "anonymous"

    if not api_key:
        # Also check Authorization: Bearer <key>
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header or Authorization: Bearer <key>.",
        )

    if not _constant_time_compare(api_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key


async def require_ws_api_key(websocket: WebSocket) -> str:
    """Authenticate WebSocket connections via query parameter or first message.

    When FORGE_API_KEY is not set, authentication is disabled (local dev mode).
    """
    configured_key = settings.api_key
    if not configured_key:
        return "anonymous"

    # Check query parameter: ws://host/ws?api_key=<key>
    api_key = websocket.query_params.get("api_key", "")

    if not api_key:
        # Check Sec-WebSocket-Protocol or X-API-Key header
        api_key = websocket.headers.get("x-api-key", "")

    if not api_key:
        auth_header = websocket.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]

    if not api_key or not _constant_time_compare(api_key, configured_key):
        await websocket.close(code=4001, reason="Authentication required")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key for WebSocket.",
        )

    return api_key


def generate_api_key() -> str:
    """Generate a cryptographically secure API key."""
    return f"forge-{secrets.token_urlsafe(32)}"
