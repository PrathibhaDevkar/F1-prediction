"""Pipeline state persistence. Plain sqlite3 (no ORM) — two small tables,
not worth adding a dependency for.
"""
import json
import os
import sqlite3
from contextlib import contextmanager

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BACKEND_DIR, "pipeline_state.db")
SEED_STATE_PATH = os.path.join(BACKEND_DIR, "seed_state.json")

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
CREATE TABLE IF NOT EXISTS track_record (
    season INTEGER NOT NULL,
    round INTEGER NOT NULL,
    event TEXT,
    driver TEXT NOT NULL,
    driver_name TEXT,
    predicted_position INTEGER,
    win_probability REAL,
    podium_probability REAL,
    points_probability REAL,
    actual_position INTEGER,
    PRIMARY KEY (season, round, driver)
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


def set_model_metrics(metrics: dict, test_predictions: list):
    """Aggregate held-out test-set metrics (MAE, AUC, etc.) plus the
    per-driver predicted-vs-actual rows behind them — recomputed fresh on
    every retrain, so this overwrites rather than accumulates."""
    set_state("model_metrics", json.dumps(metrics))
    set_state("model_test_predictions", json.dumps(test_predictions))


def get_model_metrics() -> dict | None:
    raw = get_state("model_metrics")
    return json.loads(raw) if raw else None


def get_model_test_predictions() -> list:
    raw = get_state("model_test_predictions")
    return json.loads(raw) if raw else []


def add_track_record_rows(rows: list[dict]):
    """Permanent log of real forecasts vs what actually happened, one row
    per driver per race — unlike cached_predictions (overwritten each
    retrain), this accumulates over time. Keyed on (season, round, driver)
    so re-running reconciliation for an already-recorded race updates
    rather than duplicates."""
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO track_record "
            "(season, round, event, driver, driver_name, predicted_position, "
            "win_probability, podium_probability, points_probability, actual_position) "
            "VALUES (:season, :round, :event, :driver, :driver_name, :predicted_position, "
            ":win_probability, :podium_probability, :points_probability, :actual_position) "
            "ON CONFLICT(season, round, driver) DO UPDATE SET actual_position = excluded.actual_position",
            rows,
        )
        conn.commit()


def get_track_record() -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT season, round, event, driver, driver_name, predicted_position, "
            "win_probability, podium_probability, points_probability, actual_position "
            "FROM track_record ORDER BY season DESC, round DESC"
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def seed_if_empty():
    """On a fresh pipeline_state.db with no last_processed_round yet - e.g.
    right after a cold start on a platform with no persistent disk, where
    the db is recreated empty every time - seed it from the committed
    seed_state.json snapshot so the API has real data immediately instead
    of returning nulls until the next full retrain finishes. The scheduler
    still runs normally afterward and will pick up anything newer.
    """
    if get_state("last_processed_round") is not None:
        return

    if not os.path.exists(SEED_STATE_PATH):
        return

    try:
        with open(SEED_STATE_PATH) as f:
            seed = json.load(f)
    except Exception as e:
        print(f"[db] Could not read {SEED_STATE_PATH}, skipping seed: {e}")
        return

    if seed.get("last_processed_round") is not None:
        set_state("last_processed_round", seed["last_processed_round"])
    if seed.get("model_trained_at"):
        set_state("model_trained_at", seed["model_trained_at"])

    forecast = seed.get("next_race_forecast")
    if forecast:
        set_cached_prediction(forecast["round_key"], forecast["forecast"], forecast["generatedAt"])

    if seed.get("model_metrics"):
        set_state("model_metrics", json.dumps(seed["model_metrics"]))
    if seed.get("model_test_predictions"):
        set_state("model_test_predictions", json.dumps(seed["model_test_predictions"]))
    if seed.get("track_record"):
        add_track_record_rows(seed["track_record"])

    print(f"[db] Seeded pipeline state from {SEED_STATE_PATH}")


init_db()
