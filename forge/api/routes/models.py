from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("/")
async def list_models(request: Request):
    model_router = request.app.state.model_router
    models = await model_router.list_available_models()
    return {"models": models}
