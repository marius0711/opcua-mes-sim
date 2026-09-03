import sqlite3

from fastapi.testclient import TestClient

from api.main import app
from db import store as db_store
from db.store import init_db, insert_run, insert_evaluation


def test_get_results_returns_run_summaries(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_store, "DEFAULT_DB_PATH", db_path)

    conn = sqlite3.connect(db_path)
    init_db(conn)
    run_id = insert_run(conn, arm_id="arm1", target_frequency_hz=25.0, sample_rate_hz=200.0)
    insert_evaluation(conn, run_id, "peak_frequency_hz", 25.0)
    insert_evaluation(conn, run_id, "position_std_dev", 0.1)
    insert_evaluation(conn, run_id, "torque_outlier_count", 0)
    conn.close()

    client = TestClient(app)
    response = client.get("/results")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["run_id"] == run_id
    assert data[0]["peak_frequency_hz"] == 25.0
    assert data[0]["anomaly"] is False


def test_get_results_returns_empty_list_for_missing_db(tmp_path, monkeypatch):
    db_path = tmp_path / "does_not_exist_yet.db"
    monkeypatch.setattr(db_store, "DEFAULT_DB_PATH", db_path)

    client = TestClient(app)
    response = client.get("/results")

    assert response.status_code == 200
    assert response.json() == []
