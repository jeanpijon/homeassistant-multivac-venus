"""The coordinator must mark entities unavailable when the unit stops answering."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.heat_exchanger.const import DOMAIN, STALE_AFTER_SECONDS
from custom_components.heat_exchanger.coordinator import HeatExchangerCoordinator


class FakeClient:
    def __init__(self, age):
        self.age = age

    def snapshot(self):
        return {"state": {"mode": "auto", "fan": 2}, "frame_age": self.age, "sensors": {"temperature.in_egress": 21}}


@pytest.fixture
def coordinator(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "192.0.2.2", "port": 4196})
    entry.add_to_hass(hass)
    return HeatExchangerCoordinator(hass, entry)


def test_fresh_frame_publishes_data(coordinator):
    coordinator._client = FakeClient(age=1.0)
    coordinator._publish()
    assert coordinator.last_update_success
    assert coordinator.data["sensors"]["temperature.in_egress"] == 21


def test_no_frame_yet_is_unavailable(coordinator):
    coordinator._client = FakeClient(age=None)
    coordinator._publish()
    assert not coordinator.last_update_success


def test_stale_frames_make_entities_unavailable_then_recover(coordinator):
    client = coordinator._client = FakeClient(age=1.0)
    coordinator._publish()
    assert coordinator.last_update_success

    client.age = STALE_AFTER_SECONDS + 1
    coordinator._publish()
    assert not coordinator.last_update_success

    client.age = 0.5
    coordinator._publish()
    assert coordinator.last_update_success
