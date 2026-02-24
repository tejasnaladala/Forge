from __future__ import annotations

import asyncio

import structlog

logger = structlog.get_logger()


class ChromaMemory:
    def __init__(
        self,
        persist_path: str,
        embedding_model: str = "nomic-embed-text",
        embedding_provider: str = "ollama",
        collection_name: str = "forge_memory",
    ) -> None:
        self._collection = None
        self._counter = 0

        try:
            import chromadb
            from chromadb.config import Settings

            client = chromadb.PersistentClient(
                path=persist_path,
                settings=Settings(anonymized_telemetry=False),
            )

            ef = None
            if embedding_provider == "ollama":
                try:
                    from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
                    ef = OllamaEmbeddingFunction(model_name=embedding_model)
                except Exception:
                    logger.warning("ollama_embedding_unavailable", model=embedding_model)
            elif embedding_provider == "openai":
                try:
                    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
                    ef = OpenAIEmbeddingFunction()
                except Exception:
                    logger.warning("openai_embedding_unavailable")

            kwargs = {"name": collection_name}
            if ef is not None:
                kwargs["embedding_function"] = ef

            self._collection = client.get_or_create_collection(**kwargs)

        except ImportError:
            logger.warning("chromadb_not_available")
        except Exception:
            logger.warning("chromadb_init_error", exc_info=True)

    async def store(self, session_id: str, content: str, metadata: dict | None = None) -> None:
        if self._collection is None:
            return
        self._counter += 1
        doc_id = f"{session_id}_{self._counter}"
        meta = metadata or {}
        meta["session_id"] = session_id
        collection = self._collection
        await asyncio.to_thread(collection.add, documents=[content], ids=[doc_id], metadatas=[meta])

    async def search(self, query: str, k: int = 5) -> list[str]:
        if self._collection is None:
            return []
        try:
            collection = self._collection
            results = await asyncio.to_thread(collection.query, query_texts=[query], n_results=k)
            return results.get("documents", [[]])[0]
        except Exception:
            logger.warning("chroma_search_error", exc_info=True)
            return []

    async def clear(self, session_id: str | None = None) -> None:
        if self._collection is None:
            return
        try:
            collection = self._collection
            if session_id:
                await asyncio.to_thread(collection.delete, where={"session_id": session_id})
            else:
                all_data = await asyncio.to_thread(collection.get)
                all_ids = all_data["ids"]
                if all_ids:
                    await asyncio.to_thread(collection.delete, ids=all_ids)
        except Exception:
            logger.warning("chroma_clear_error", exc_info=True)
