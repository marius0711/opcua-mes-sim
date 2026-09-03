import pytest

from opcua_client.client import validate_target_frequency, MAX_VIBRATION_FREQUENCY_HZ


def test_validate_target_frequency_accepts_value_at_limit():
    validate_target_frequency(MAX_VIBRATION_FREQUENCY_HZ)


def test_validate_target_frequency_accepts_value_below_limit():
    validate_target_frequency(MAX_VIBRATION_FREQUENCY_HZ - 10)


def test_validate_target_frequency_rejects_value_above_limit():
    with pytest.raises(ValueError):
        validate_target_frequency(MAX_VIBRATION_FREQUENCY_HZ + 1)
