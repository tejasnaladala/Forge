from __future__ import annotations

from fastapi import APIRouter

from forge.version import __version__

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "forge", "version": __version__}
