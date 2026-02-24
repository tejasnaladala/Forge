from __future__ import annotations

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

            client = chromadb.Client(chromadb.config.Settings(
                persist_directory=persist_path,
                anonymized_telemetry=False,
            ))

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
        self._collection.add(documents=[content], ids=[doc_id], metadatas=[meta])

    async def search(self, query: str, k: int = 5) -> list[str]:
        if self._collection is None:
            return []
        try:
            results = self._collection.query(query_texts=[query], n_results=k)
            return results.get("documents", [[]])[0]
        except Exception:
            logger.warning("chroma_search_error", exc_info=True)
            return []

    async def clear(self, session_id: str | None = None) -> None:
        if self._collection is None:
            return
        try:
            if session_id:
                self._collection.delete(where={"session_id": session_id})
            else:
                # Reset by getting all IDs
                all_ids = self._collection.get()["ids"]
                if all_ids:
                    self._collection.delete(ids=all_ids)
        except Exception:
            logger.warning("chroma_clear_error", exc_info=True)
