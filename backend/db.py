"""Pipeline state persistence. Plain sqlite3 (no ORM) — two small tables,
not worth adding a dependency for.
"""
import json
import os
import sqlite3
from contextlib import contextmanager

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BACKEND_DIR, "pipeline_state.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS pipeline_state (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS cached_predictions (
    round_key TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    generated_at TEXT NOT NULL
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def get_state(key: str, default=None):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM pipeline_state WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default


def set_state(key: str, value):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO pipeline_state (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
        conn.commit()


def set_cached_prediction(round_key: str, forecast: list, generated_at: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cached_predictions (round_key, payload, generated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(round_key) DO UPDATE SET payload = excluded.payload, generated_at = excluded.generated_at",
            (round_key, json.dumps(forecast), generated_at),
        )
        conn.commit()


def get_cached_prediction(round_key: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT payload, generated_at FROM cached_predictions WHERE round_key = ?",
            (round_key,),
        ).fetchone()
        if not row:
            return None
        return {"forecast": json.loads(row[0]), "generatedAt": row[1]}


init_db()
