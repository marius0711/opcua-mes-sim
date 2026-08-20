from report.report import flag_anomalies, format_report


def test_flag_anomalies_flags_deviating_run():
    summaries = [
        {"run_id": 1, "peak_frequency_hz": 25.0},
        {"run_id": 2, "peak_frequency_hz": 24.5},
        {"run_id": 3, "peak_frequency_hz": 40.0},
    ]

    flagged = flag_anomalies(summaries)

    assert flagged[0]["anomaly"] is False
    assert flagged[1]["anomaly"] is False
    assert flagged[2]["anomaly"] is True


def test_flag_anomalies_no_anomaly_when_all_close():
    summaries = [
        {"run_id": 1, "peak_frequency_hz": 25.0},
        {"run_id": 2, "peak_frequency_hz": 25.5},
    ]

    flagged = flag_anomalies(summaries)

    assert all(not s["anomaly"] for s in flagged)


def test_format_report_includes_anomaly_marker():
    summaries = [
        {"run_id": 1, "started_at": "2026-01-01", "target_frequency_hz": 25.0,
         "peak_frequency_hz": 25.0, "position_std_dev": 0.1,
         "torque_outlier_count": 0, "anomaly": False},
        {"run_id": 2, "started_at": "2026-01-01", "target_frequency_hz": 40.0,
         "peak_frequency_hz": 40.0, "position_std_dev": 0.1,
         "torque_outlier_count": 2, "anomaly": True},
    ]

    output = format_report(summaries)

    assert "ANOMALY" in output
    assert output.count("Run") == 2
