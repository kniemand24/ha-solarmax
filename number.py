# custom_components/solarmax/number.py
from __future__ import annotations
from typing import Tuple

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, TYPE_RANGES, DEFAULT_RANGES
from .coordinator import SolarMaxDataCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Setzt die Number-Entitäten (Regler) auf."""
    coordinator: SolarMaxDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    din = entry.data["din"]

    # Typ-Ermittlung für die Slider-Bereiche
    raw_data = coordinator.data if coordinator.data else {}
    typ = int(raw_data.get("TYP", 0))
    ranges = TYPE_RANGES.get(typ, DEFAULT_RANGES)

    entities = [
        SolarMaxNumber(coordinator, entry, din, "PLR", "Power Limit", "%", ranges["PLR"]),
        SolarMaxNumber(coordinator, entry, din, "PAM", "AC Output Max", "W", ranges["PAM"]),
        SolarMaxNumber(coordinator, entry, din, "PIN", "Installed Capacity", "W", ranges["PIN"]),
        SolarMaxNumber(coordinator, entry, din, "IAA", "AC Output Max IAA", "%", ranges["IAA"]),
    ]
    async_add_entities(entities)

class SolarMaxNumber(CoordinatorEntity, NumberEntity):
    """Regler-Entität mit Istwert-Anzeige in den Attributen."""
    
    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, entry, din, key, name, unit, ranges):
        super().__init__(coordinator)
        self._entry = entry
        self._din = din
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"solarmax_{din}_set_{key.lower()}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = float(ranges[0])
        self._attr_native_max_value = float(ranges[1])
        self._attr_native_step = 1.0

    @property
    def native_value(self) -> float | None:
        """Sollwert aus dem Coordinator (umgerechnet)."""
        if not self.coordinator.data: return None
        val = self.coordinator.data.get(self._key)
        if val is None: return None
        
        # Umrechnung für Anzeige (Sollwert)
        if self._key in ["PAM", "PIN"]:
            return float(val) / 2.0
        return float(val)

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Hier betten wir den echten Istwert ein."""
        attrs = {}
        if self.coordinator.data:
            ist_val = self.coordinator.data.get(self._key)
            if ist_val is not None:
                # Wir berechnen den Wert für das Attribut genauso wie den Hauptwert
                display_val = float(ist_val) / 2.0 if self._key in ["PAM", "PIN"] else float(ist_val)
                attrs["current_measured_value"] = display_val
                attrs["unit"] = self._attr_native_unit_of_measurement
                # Ein sprechender Name für das UI
                attrs["status"] = f"Inverter meldet {display_val} {self._attr_native_unit_of_measurement}"
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._din)},
            name=f"SolarMax {self._din}",
        )

    async def async_set_native_value(self, value: float) -> None:
        """Schreibt den Wert und triggert Refresh."""
        svc = {"PLR": "set_power_limit", "PAM": "set_pam", "PIN": "set_pin", "IAA": "set_iaa"}[self._key]

        await self.hass.services.async_call(
            DOMAIN, svc, {"value": int(round(value)), "entry_id": self._entry.entry_id},
            blocking=True,
        )
        await self.coordinator.async_request_refresh()
        
