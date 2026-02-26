# custom_components/solarmax/config_flow.py
# Version 0.0.8

from __future__ import annotations
import logging
from typing import Any
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
import voluptuous as vol
from .const import DOMAIN, DEFAULT_PORT, DEFAULT_ADDRESS, FULL_KEYS
from .client import SolarMaxClient
from .protocol import build_read

_LOGGER = logging.getLogger(__name__)

class SolarMaxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            client = SolarMaxClient(host, DEFAULT_PORT, DEFAULT_ADDRESS)
            try:
                t_din = build_read("FB", DEFAULT_ADDRESS, ["DIN"])
                _LOGGER.debug("SolarMax DIN request: %s", t_din)
                resp = await client.send(t_din, timeout=5.0)
                din = resp.get("data", {}).get("DIN")

                if not din:
                    t_full = build_read("FB", DEFAULT_ADDRESS, FULL_KEYS)
                    _LOGGER.debug("SolarMax FULL request: %s", t_full)
                    resp = await client.send(t_full, timeout=6.0)
                    din = resp.get("data", {}).get("DIN")

                if not din:
                    errors["base"] = "invalid_response"
                else:
                    await self.async_set_unique_id(str(din))
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"SolarMax {din}",
                        data={
                            "host": host,
                            "address": DEFAULT_ADDRESS,
                            "port": DEFAULT_PORT,
                            "din": str(din),
                        },
                    )
            except Exception as ex:
                _LOGGER.exception("SolarMaxConfigFlow: Fehler bei DIN-Abfrage: %s", ex)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )
