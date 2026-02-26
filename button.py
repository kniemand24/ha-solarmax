# custom_components/solarmax/button.py
# Version 0.0.8

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Setzt den Force-Update Button auf."""
    # Wir holen uns den existierenden Coordinator aus den HA-Daten
    # (Stelle sicher, dass er in der __init__.py unter hass.data abgelegt wurde)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    din = entry.data["din"]

    async_add_entities([SolarMaxForceUpdateButton(coordinator, din)])

class SolarMaxForceUpdateButton(ButtonEntity):
    """Button um einen vollen Daten-Scan zu erzwingen."""

    def __init__(self, coordinator, din):
        self.coordinator = coordinator
        self._din = din
        self._attr_name = "Vollständigen Scan erzwingen"
        self._attr_unique_id = f"solarmax_force_update_{din}"
        self._attr_icon = "mdi:refresh-circle"

    async def async_press(self) -> None:
        """Aktion wenn der Button gedrückt wird."""
        await self.coordinator.force_full_update()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._din)},
            name=f"SolarMax {self._din}",
        )
