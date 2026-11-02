from __future__ import annotations
import asyncio, contextlib, logging
from typing import Any
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, DEFAULT_POLL_SECONDS, CONF_HOST, CONF_PORT
from .client import RS485IPClient

_LOGGER = logging.getLogger(__name__)

async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)

class HeatExchangerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.entry = entry
        self._client: RS485IPClient | None = None
        self._task: asyncio.Task | None = None

    async def async_init(self) -> None:
        cfg = {**self.entry.data, **(self.entry.options or {})}
        self._client = RS485IPClient(host=cfg[CONF_HOST], port=int(cfg[CONF_PORT]), poll_seconds=DEFAULT_POLL_SECONDS)
        await self.hass.async_add_executor_job(self._client.start)
        self._task = self.hass.loop.create_task(self._pump())
        if not hasattr(self.entry, "_hx_listener_added"):
            self.entry.add_update_listener(_async_options_updated)
            setattr(self.entry, "_hx_listener_added", True)

    async def _pump(self) -> None:
        try:
            while True:
                await asyncio.sleep(1)
                if self._client:
                    self.async_set_updated_data(self._client.snapshot())
        except asyncio.CancelledError:
            pass

    async def async_shutdown(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(Exception):
                await self._task
        if self._client:
            await self.hass.async_add_executor_job(self._client.stop)

    async def async_set_mode(self, ha_mode: str) -> None:
        if not self._client:
            return
        await self.hass.async_add_executor_job(self._client.set_mode, ha_mode)
        snap = self._client.snapshot()
        # leaving off with fan 0 -> bump to 1 for auto/cool
        if ha_mode != "off" and snap.get("state", {}).get("fan", 0) == 0:
            await self.hass.async_add_executor_job(self._client.set_fan_level, 1)

    async def async_set_fan_level(self, level_str: str) -> None:
        if not self._client:
            return
        try:
            level = int(level_str)
        except Exception:
            level = 0
        # If user sets level 0, also set mode to off
        if level == 0:
            await self.hass.async_add_executor_job(self._client.set_mode, "off")
        await self.hass.async_add_executor_job(self._client.set_fan_level, level)
