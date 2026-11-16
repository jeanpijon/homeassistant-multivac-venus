from __future__ import annotations
from typing import Any
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, FAN_LEVELS, MANUFACTURER, MODEL, DEVICE_NAME
from .coordinator import HeatExchangerCoordinator

HVAC_LIST = [HVACMode.OFF, HVACMode.AUTO, HVACMode.COOL]

async def async_setup_entry(hass, entry, async_add_entities):
    coord: HeatExchangerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HXClimate(coord)])

class HXClimate(CoordinatorEntity[HeatExchangerCoordinator], ClimateEntity):
    _attr_name = "Venus Heat Exchanger"
    _attr_supported_features = ClimateEntityFeature.FAN_MODE
    _attr_hvac_modes = HVAC_LIST
    _attr_fan_modes = list(FAN_LEVELS)  # now includes "0"
    # Home Assistant 2026.11 renamed the climate unit attribute; older releases only know the old one.
    if hasattr(ClimateEntity, "native_temperature_unit"):
        _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    else:
        _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: HeatExchangerCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_climate"

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
    def hvac_mode(self) -> HVACMode | None:
        mode = (self.coordinator.data or {}).get("state", {}).get("mode", "off")
        try:
            return HVACMode(mode)
        except Exception:
            return HVACMode.OFF

    @property
    def fan_mode(self) -> str | None:
        return str((self.coordinator.data or {}).get("state", {}).get("fan", 0)) if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("sensors", {})

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self.coordinator.async_set_mode(hvac_mode.value)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if fan_mode not in FAN_LEVELS:
            return
        await self.coordinator.async_set_fan_level(fan_mode)
