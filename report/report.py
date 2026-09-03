import sqlite3
from statistics import median

from db.store import DEFAULT_DB_PATH

DEVIATION_THRESHOLD = 0.2

SUMMARY_QUERY = """
SELECT
    r.run_id,
    r.started_at,
    r.target_frequency_hz,
    MAX(CASE WHEN e.metric = 'peak_frequency_hz' THEN e.value END) AS peak_frequency_hz,
    MAX(CASE WHEN e.metric = 'position_std_dev' THEN e.value END) AS position_std_dev,
    MAX(CASE WHEN e.metric = 'torque_outlier_count' THEN e.value END) AS torque_outlier_count
FROM measurement_run r
JOIN evaluation_result e ON e.run_id = r.run_id
GROUP BY r.run_id
ORDER BY r.run_id
"""


def fetch_run_summaries(conn):
    columns = [
        "run_id", "started_at", "target_frequency_hz",
        "peak_frequency_hz", "position_std_dev", "torque_outlier_count",
    ]
    rows = conn.execute(SUMMARY_QUERY).fetchall()
    return [dict(zip(columns, row)) for row in rows]


def flag_anomalies(summaries, threshold=DEVIATION_THRESHOLD):
    if not summaries:
        return summaries
    peaks = [s["peak_frequency_hz"] for s in summaries]
    baseline = median(peaks)
    for s in summaries:
        deviation = abs(s["peak_frequency_hz"] - baseline) / baseline if baseline else 0.0
        s["anomaly"] = deviation > threshold
    return summaries


def format_report(summaries):
    lines = []
    for s in summaries:
        marker = " <-- ANOMALY" if s["anomaly"] else ""
        lines.append(
            f"Run {s['run_id']} ({s['started_at']}): "
            f"target={s['target_frequency_hz']:.1f} Hz, "
            f"peak={s['peak_frequency_hz']:.2f} Hz, "
            f"position_std_dev={s['position_std_dev']:.3f}, "
            f"torque_outliers={int(s['torque_outlier_count'])}{marker}"
        )
    return "\n".join(lines)


def main():
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    summaries = fetch_run_summaries(conn)
    summaries = flag_anomalies(summaries)
    print(format_report(summaries))
    conn.close()


if __name__ == "__main__":
    main()
