"""Frame parsing and command table of the RS485 client (no serial port involved)."""
from __future__ import annotations

import pytest

from custom_components.heat_exchanger.client import COMMANDS, RS485IPClient, parse_sensor_frame


def make_frame(values: list[int], header: bytes = b"A" * 19) -> bytes:
    """19-byte header + ASCII hex payload + 1 trailing byte, like the unit sends."""
    return header + "".join(f"{v:02X}" for v in values).encode() + b"\r"


def payload(**overrides: int) -> list[int]:
    values = [0] * 27
    values[1], values[2] = 55, 60
    values[19], values[20], values[21], values[22] = 5, 12, 21, 19
    for index, value in overrides.items():
        values[int(index.lstrip("v"))] = value
    return values


def test_parses_temperatures_and_fans():
    sensors = parse_sensor_frame(make_frame(payload()))
    assert sensors == {
        "power_factor.fan_ingress": 55,
        "power_factor.fan_egress": 60,
        "temperature.out_ingress": 5,
        "temperature.out_egress": 12,
        "temperature.in_egress": 21,
        "temperature.in_ingress": 19,
    }


def test_short_reply_is_rejected():
    assert parse_sensor_frame(b"") is None
    assert parse_sensor_frame(b"x" * 39) is None


def test_non_hex_payload_is_rejected():
    assert parse_sensor_frame(b"A" * 19 + b"ZZ" * 25 + b"\r") is None


def test_non_utf8_payload_is_rejected():
    assert parse_sensor_frame(b"A" * 19 + b"\xff" * 30 + b"\r") is None


def test_too_few_values_is_rejected():
    assert parse_sensor_frame(make_frame([1] * 22)) is None


def test_every_reachable_mode_has_a_command():
    for mode in ("cool", "auto"):
        for level in (1, 2, 3):
            assert f"{mode}_{level}" in COMMANDS
    assert "idle_0" in COMMANDS


def test_commands_are_uniform_frames():
    lengths = {len(cmd) for cmd in COMMANDS.values()}
    assert len(lengths) == 1
    assert all(cmd[-1] == ord("\r") for cmd in COMMANDS.values())


@pytest.fixture
def client():
    return RS485IPClient("192.0.2.2", 4196, 1.0)


def test_fan_level_is_clamped(client):
    client.set_fan_level(9)
    assert client.snapshot()["state"]["fan"] == 3
    client.set_fan_level(-4)
    assert client.snapshot()["state"]["fan"] == 0


def test_idle_resets_fan_and_reports_off(client):
    client.set_mode("cool")
    client.set_fan_level(2)
    assert client.snapshot()["state"] == {"mode": "cool", "fan": 2}
    client.set_mode("off")
    assert client.snapshot()["state"] == {"mode": "off", "fan": 0}


def test_snapshot_has_no_frame_age_before_first_frame(client):
    assert client.snapshot()["frame_age"] is None


def test_climate_declares_its_unit_the_way_this_home_assistant_expects():
    # _attr_temperature_unit is deprecated from Home Assistant 2026.11 (removed in 2027.11);
    # older releases only know it. The entity picks whichever the base class supports.
    from homeassistant.components.climate import ClimateEntity

    from custom_components.heat_exchanger.climate import HXClimate

    declared = vars(HXClimate)  # Home Assistant wraps _attr_* in cached properties, so check names
    if hasattr(ClimateEntity, "native_temperature_unit"):
        assert "_attr_native_temperature_unit" in declared
        assert "_attr_temperature_unit" not in declared
    else:
        assert "_attr_temperature_unit" in declared
