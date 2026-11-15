"""Power-outage behaviour: the unit or its gateway is not there when Home Assistant starts."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.heat_exchanger.const import DOMAIN


class FakeClient:
    age = None  # None: no frame received yet

    def __init__(self, host, port, poll_seconds):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def set_mode(self, mode):
        pass

    def set_fan_level(self, level):
        pass

    def snapshot(self):
        return {
            "state": {"mode": "auto", "fan": 2},
            "frame_age": FakeClient.age,
            "sensors": {
                "temperature.out_ingress": 5, "temperature.out_egress": 12,
                "temperature.in_egress": 21, "temperature.in_ingress": 19,
                "power_factor.fan_ingress": 55, "power_factor.fan_egress": 60,
            },
        }


@pytest.fixture
async def entry(hass):
    FakeClient.age = None
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "192.0.2.2", "port": 4196})
    entry.add_to_hass(hass)
    with patch("custom_components.heat_exchanger.coordinator.RS485IPClient", FakeClient):
        yield entry
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


def states(hass):
    return [s for domain in ("sensor", "climate") for s in hass.states.async_all(domain)]


async def test_loads_with_no_unit_and_comes_up_when_it_answers(hass, entry):
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    # Nothing has answered yet: entities exist but say so.
    assert len(states(hass)) == 7
    assert {s.state for s in states(hass)} == {"unavailable"}

    # The unit boots and starts answering: no reload, no restart needed.
    FakeClient.age = 0.5
    hass.data[DOMAIN][entry.entry_id]._publish()
    await hass.async_block_till_done()
    assert "unavailable" not in {s.state for s in states(hass)}
    assert "21" in {s.state for s in states(hass)}  # the in_egress temperature
