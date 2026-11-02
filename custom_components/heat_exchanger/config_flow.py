from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from .const import DOMAIN, CONF_HOST, CONF_PORT

DEFAULT_TITLE = "MultiVac Venus"

DATA_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME, default=DEFAULT_TITLE): str,
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT, default=8899): int,
})

class HeatExchangerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            title = user_input.get(CONF_NAME, DEFAULT_TITLE)
            data = {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
            options = data.copy()
            return self.async_create_entry(title=title, data=data, options=options)
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors={})

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return HeatExchangerOptionsFlow(config_entry)

class HeatExchangerOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        cur = {**self.entry.data, **(self.entry.options or {})}
        schema = vol.Schema({
            vol.Required(CONF_HOST, default=cur.get(CONF_HOST, "192.168.1.50")): str,
            vol.Required(CONF_PORT, default=cur.get(CONF_PORT, 8899)): int,
        })
        return self.async_show_form(step_id="init", data_schema=schema, errors={})
