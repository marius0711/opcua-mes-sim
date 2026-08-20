import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path(
    os.environ.get("OPCUA_MES_DB_PATH", str(Path(__file__).parent.parent / "opcua_mes_sim.db"))
)
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


def insert_run(conn, arm_id, target_frequency_hz, sample_rate_hz):
    cursor = conn.execute(
        "INSERT INTO measurement_run (arm_id, started_at, target_frequency_hz, sample_rate_hz) "
        "VALUES (?, ?, ?, ?)",
        (arm_id, datetime.now(timezone.utc).isoformat(), target_frequency_hz, sample_rate_hz),
    )
    conn.commit()
    return cursor.lastrowid


def insert_points(conn, run_id, sensor, values, timestamps):
    conn.executemany(
        "INSERT INTO measurement_point (run_id, sensor, t, value) VALUES (?, ?, ?, ?)",
        [(run_id, sensor, t, v) for t, v in zip(timestamps, values)],
    )
    conn.commit()


def insert_evaluation(conn, run_id, metric, value):
    conn.execute(
        "INSERT INTO evaluation_result (run_id, metric, value) VALUES (?, ?, ?)",
        (run_id, metric, value),
    )
    conn.commit()
