from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
import structlog

logger = structlog.get_logger()


class SQLiteMemory:
    def __init__(self, persist_path: str) -> None:
        path = Path(persist_path)
        path.mkdir(parents=True, exist_ok=True)
        self._db_path = str(path / "memory.db")
        self._init_db_sync()

    def _init_db_sync(self) -> None:
        """Synchronous init for use in __init__."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON memories(session_id)")
        conn.commit()
        conn.close()

    async def store(self, session_id: str, content: str, metadata: dict | None = None) -> None:
        async with aiosqlite.connect(self._db_path) as conn:
            await conn.execute(
                "INSERT INTO memories (session_id, content, metadata, created_at) VALUES (?, ?, ?, ?)",
                (session_id, content, json.dumps(metadata or {}), datetime.now(timezone.utc).isoformat()),
            )
            await conn.commit()

    async def get_recent(self, session_id: str, limit: int = 10) -> list[str]:
        async with aiosqlite.connect(self._db_path) as conn:
            cursor = await conn.execute(
                "SELECT content FROM memories WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def clear(self, session_id: str | None = None) -> None:
        async with aiosqlite.connect(self._db_path) as conn:
            if session_id:
                await conn.execute("DELETE FROM memories WHERE session_id = ?", (session_id,))
            else:
                await conn.execute("DELETE FROM memories")
            await conn.commit()
