import numpy as np


def find_vibration_peak(samples, sample_rate_hz):
    n = len(samples)
    windowed = np.asarray(samples) * np.hanning(n)
    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate_hz)

    spectrum[0] = 0.0  # drop DC offset so it can't win the peak search
    peak_idx = int(np.argmax(spectrum))

    return {
        "peak_frequency_hz": float(freqs[peak_idx]),
        "peak_magnitude": float(spectrum[peak_idx]),
    }


def position_repeatability(samples):
    return {
        "mean": float(np.mean(samples)),
        "std_dev": float(np.std(samples)),
    }


def detect_outliers(samples, z_threshold=3.0):
    samples = np.asarray(samples)
    mean = np.mean(samples)
    std = np.std(samples)
    if std == 0:
        return []
    z_scores = (samples - mean) / std
    return [int(i) for i in np.where(np.abs(z_scores) > z_threshold)[0]]
