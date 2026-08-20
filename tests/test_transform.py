import numpy as np

from opcua_client.transform import find_vibration_peak, position_repeatability, detect_outliers


def test_find_vibration_peak_detects_known_frequency():
    sample_rate_hz = 200
    duration_s = 2.0
    target_freq_hz = 40.0
    t = np.arange(0, duration_s, 1.0 / sample_rate_hz)
    signal = np.sin(2 * np.pi * target_freq_hz * t)

    result = find_vibration_peak(signal, sample_rate_hz)

    assert abs(result["peak_frequency_hz"] - target_freq_hz) < 1.0


def test_position_repeatability_reports_zero_std_for_constant_signal():
    result = position_repeatability([5.0, 5.0, 5.0, 5.0])

    assert result["mean"] == 5.0
    assert result["std_dev"] == 0.0


def test_detect_outliers_flags_single_spike():
    samples = [5.0] * 20 + [50.0]

    outliers = detect_outliers(samples)

    assert outliers == [20]


def test_detect_outliers_returns_empty_for_constant_signal():
    outliers = detect_outliers([5.0] * 10)

    assert outliers == []
