from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import structlog

logger = structlog.get_logger()


class SQLiteMemory:
    def __init__(self, persist_path: str) -> None:
        path = Path(persist_path)
        path.mkdir(parents=True, exist_ok=True)
        self._db_path = str(path / "memory.db")
        self._init_db()

    def _init_db(self) -> None:
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
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "INSERT INTO memories (session_id, content, metadata, created_at) VALUES (?, ?, ?, ?)",
            (session_id, content, json.dumps(metadata or {}), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()

    async def get_recent(self, session_id: str, limit: int = 10) -> list[str]:
        conn = sqlite3.connect(self._db_path)
        cursor = conn.execute(
            "SELECT content FROM memories WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results

    async def clear(self, session_id: str | None = None) -> None:
        conn = sqlite3.connect(self._db_path)
        if session_id:
            conn.execute("DELETE FROM memories WHERE session_id = ?", (session_id,))
        else:
            conn.execute("DELETE FROM memories")
        conn.commit()
        conn.close()
