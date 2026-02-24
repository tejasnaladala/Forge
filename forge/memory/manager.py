from __future__ import annotations

import structlog

from forge.core.types import MemoryConfig
from forge.memory.backends.sqlite import SQLiteMemory

logger = structlog.get_logger()


class MemoryManager:
    def __init__(self, config: MemoryConfig) -> None:
        self._config = config
        self._sqlite = SQLiteMemory(config.persist_path)
        self._chroma = None

        if config.backend == "chroma":
            try:
                from forge.memory.backends.chroma import ChromaMemory
                self._chroma = ChromaMemory(
                    persist_path=config.persist_path,
                    embedding_model=config.embedding_model,
                    embedding_provider=config.embedding_provider,
                )
            except Exception:
                logger.warning("chroma_init_failed", exc_info=True)

    async def store(
        self,
        session_id: str,
        content: str,
        memory_type: str = "episodic",
        metadata: dict | None = None,
    ) -> None:
        try:
            await self._sqlite.store(session_id, content, metadata)
            if self._chroma and memory_type == "episodic":
                await self._chroma.store(session_id, content, metadata)
        except Exception:
            logger.warning("memory_store_error", exc_info=True)

    async def retrieve(
        self,
        session_id: str,
        query: str,
        k: int = 5,
        memory_type: str = "semantic",
    ) -> list[str]:
        try:
            if self._chroma and memory_type == "semantic":
                return await self._chroma.search(query, k=k)
            return await self._sqlite.get_recent(session_id, limit=k)
        except Exception:
            logger.warning("memory_retrieve_error", exc_info=True)
            return []

    async def clear(self, session_id: str | None = None) -> None:
        try:
            await self._sqlite.clear(session_id)
            if self._chroma:
                await self._chroma.clear(session_id)
        except Exception:
            logger.warning("memory_clear_error", exc_info=True)
