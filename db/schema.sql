CREATE TABLE IF NOT EXISTS measurement_run (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    arm_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    target_frequency_hz REAL NOT NULL,
    sample_rate_hz REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS measurement_point (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES measurement_run(run_id),
    sensor TEXT NOT NULL,
    t REAL NOT NULL,
    value REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluation_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES measurement_run(run_id),
    metric TEXT NOT NULL,
    value REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_measurement_point_run ON measurement_point(run_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_result_run ON evaluation_result(run_id);
