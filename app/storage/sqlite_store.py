from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.core.models import TicketData


class SQLiteStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    audio_path TEXT,
                    transcript TEXT NOT NULL,
                    ticket_json TEXT NOT NULL,
                    submitted INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    transcript TEXT NOT NULL,
                    final_ticket_json TEXT NOT NULL,
                    category_code TEXT NOT NULL
                )
                """
            )

    def save_ticket(self, audio_path: str, transcript: str, ticket: TicketData, submitted: bool) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tickets (created_at, audio_path, transcript, ticket_json, submitted)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    audio_path,
                    transcript,
                    ticket.model_dump_json(ensure_ascii=False),
                    1 if submitted else 0,
                ),
            )
            return int(cursor.lastrowid)

    def save_feedback(self, transcript: str, final_ticket: TicketData) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO learning_feedback (created_at, transcript, final_ticket_json, category_code)
                VALUES (?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    transcript,
                    final_ticket.model_dump_json(ensure_ascii=False),
                    final_ticket.categorie_code,
                ),
            )

    def get_recent_feedback(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT transcript, final_ticket_json, category_code
                FROM learning_feedback
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        result: list[dict] = []
        for transcript, final_ticket_json, category_code in rows:
            result.append(
                {
                    "transcript": transcript,
                    "ticket": json.loads(final_ticket_json),
                    "category_code": category_code,
                }
            )
        return result
