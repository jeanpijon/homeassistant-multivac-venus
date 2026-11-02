from __future__ import annotations
from typing import Any
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, SENSOR_MAP, MANUFACTURER, MODEL, DEVICE_NAME
from .coordinator import HeatExchangerCoordinator

async def async_setup_entry(hass, entry, async_add_entities):
    coord: HeatExchangerCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [HXSensor(coord, key) for key in SENSOR_MAP]
    async_add_entities(sensors)

class HXSensor(CoordinatorEntity[HeatExchangerCoordinator], SensorEntity):
    def __init__(self, coordinator: HeatExchangerCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        unit, devclass = SENSOR_MAP[key]
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = devclass
        self._attr_name = f"Venus {key.replace('.', ' ').title()}"

    @property
    def device_info(self) -> DeviceInfo:
        client = getattr(self.coordinator, "_client", None)
        ident = getattr(client, "identifier", "venus-unknown") if client else "venus-unknown"
        return DeviceInfo(
            identifiers={(DOMAIN, ident)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=DEVICE_NAME,
            suggested_area="Technická místnost",
        )

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        return data.get("sensors", {}).get(self._key)
