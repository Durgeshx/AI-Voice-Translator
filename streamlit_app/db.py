"""SQLite persistence for saved conversations."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_FILE = str(Path(__file__).parent / "conversation_history.db")


def _conn():
    return sqlite3.connect(DB_FILE)


def init_db():
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                speaker TEXT,
                english TEXT,
                translation TEXT,
                sentiment TEXT,
                score REAL
            )
            """
        )


def save_history(history: list[dict]):
    if not history:
        return 0
    init_db()
    inserted = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as c:
        cur = c.cursor()
        for item in history:
            cur.execute(
                "SELECT id FROM conversations WHERE speaker=? AND english=? AND translation=? LIMIT 1",
                (item["speaker"], item["english"], item["translation"]),
            )
            if cur.fetchone():
                continue
            cur.execute(
                """INSERT INTO conversations
                (created_at, speaker, english, translation, sentiment, score)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    now,
                    item["speaker"],
                    item["english"],
                    item["translation"],
                    item.get("sentiment", "NEU"),
                    float(item.get("score", 0.0)),
                ),
            )
            inserted += 1
    return inserted


def load_history(search: str = "", limit: int = 30) -> list[dict]:
    init_db()
    with _conn() as c:
        cur = c.cursor()
        if search:
            like = f"%{search}%"
            cur.execute(
                """SELECT created_at, speaker, english, translation, sentiment, score
                   FROM conversations
                   WHERE speaker LIKE ? OR english LIKE ? OR translation LIKE ?
                   ORDER BY id DESC LIMIT ?""",
                (like, like, like, limit),
            )
        else:
            cur.execute(
                """SELECT created_at, speaker, english, translation, sentiment, score
                   FROM conversations ORDER BY id DESC LIMIT ?""",
                (limit,),
            )
        rows = cur.fetchall()
    return [
        dict(
            created_at=r[0],
            speaker=r[1],
            english=r[2],
            translation=r[3],
            sentiment=r[4] or "NEU",
            score=float(r[5] or 0.0),
        )
        for r in rows
    ]


def clear_history():
    init_db()
    with _conn() as c:
        c.execute("DELETE FROM conversations")
