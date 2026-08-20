import sqlite3

import pytest

from db.store import init_db, insert_run, insert_points, insert_evaluation


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    init_db(connection)
    yield connection
    connection.close()


def test_insert_run_returns_run_id(conn):
    run_id = insert_run(conn, arm_id="arm1", target_frequency_hz=25.0, sample_rate_hz=200.0)

    assert run_id == 1


def test_insert_points_round_trip(conn):
    run_id = insert_run(conn, arm_id="arm1", target_frequency_hz=25.0, sample_rate_hz=200.0)

    insert_points(conn, run_id, sensor="vibration", values=[0.1, 0.2], timestamps=[0.0, 0.005])

    rows = conn.execute(
        "SELECT sensor, t, value FROM measurement_point WHERE run_id = ?", (run_id,)
    ).fetchall()
    assert rows == [("vibration", 0.0, 0.1), ("vibration", 0.005, 0.2)]


def test_insert_evaluation_round_trip(conn):
    run_id = insert_run(conn, arm_id="arm1", target_frequency_hz=25.0, sample_rate_hz=200.0)

    insert_evaluation(conn, run_id, metric="peak_frequency_hz", value=24.66)

    row = conn.execute(
        "SELECT metric, value FROM evaluation_result WHERE run_id = ?", (run_id,)
    ).fetchone()
    assert row == ("peak_frequency_hz", 24.66)
