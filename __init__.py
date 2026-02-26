# custom_components/solarmax/__init__.py
# Version 0.0.9

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .coordinator import SolarMaxDataCoordinator
from .const import DOMAIN, PLATFORMS
from .client import SolarMaxClient
from .protocol import build_write


_LOGGER = logging.getLogger(__name__)

# Service-Namen
SERVICE_SET_POWER_LIMIT = "set_power_limit"  # PLR (%)
SERVICE_SET_PAM = "set_pam"                  # PAM (W)
SERVICE_SET_PIN = "set_pin"                  # PIN (W)
SERVICE_SET_IAA = "set_iaa"                  # IAA (%)

# Gemeinsame Felder
COMMON_FIELDS = {
    vol.Optional("entry_id"): cv.string,  # falls mehrere Inverter
    vol.Optional("din"): cv.string,       # alternativ über Seriennummer
}

# Schemas (Nutzerwerte; echte W/%) – Grenzen validieren wir im Number-Entity präzise,
# für Services bleiben wir bewusst großzügig, um Automationen nicht zu blocken.
SERVICE_SCHEMA_SET_POWER_LIMIT = vol.Schema({
    vol.Required("value"): vol.All(int, vol.Range(min=0, max=100)),
    **COMMON_FIELDS,
})
SERVICE_SCHEMA_SET_IAA = vol.Schema({
    vol.Required("value"): vol.All(int, vol.Range(min=0, max=100)),
    **COMMON_FIELDS,
})
SERVICE_SCHEMA_SET_PAM = vol.Schema({
    vol.Required("value"): vol.All(int, vol.Range(min=0, max=10000)),  # echte Watt
    **COMMON_FIELDS,
})
SERVICE_SCHEMA_SET_PIN = vol.Schema({
    vol.Required("value"): vol.All(int, vol.Range(min=0, max=20000)),  # echte Watt
    **COMMON_FIELDS,
})

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up this integration using YAML is not supported."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die SolarMax Integration über die UI auf."""
    host = entry.data.get("host")
    port = entry.data.get("port")
    address = entry.data.get("address", "01")
    din = entry.data.get("din", "Unknown")

    # Wir übergeben jetzt host und port statt einer festen Client-Instanz
    coordinator = SolarMaxDataCoordinator(hass, address, din, host, port)

    # Erster Datenabruf
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Erstelle die Sensoren
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entlädt die Integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
