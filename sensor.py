# custom_components/solarmax/sensor.py
# Version 0.0.8

from __future__ import annotations
import logging
import asyncio
from datetime import timedelta

from .coordinator import SolarMaxDataCoordinator # Importiere den Coordinator
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
# # # from homeassistant.helpers.update_coordinator import (
# # #     CoordinatorEntity,
# # #     DataUpdateCoordinator,
# # #     UpdateFailed,
# # # )

from .const import (
    DOMAIN, SYS_MAP, TYP_MAP, SAL_MAP, MEAS_MAP, 
    translate_bitmask
)
from .client import SolarMaxClient
from .protocol import build_read

_LOGGER = logging.getLogger(__name__)

# "Eingang" zur Sensor-Plattform
async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    # Holen den fertigen Coordinator aus hass.data
    coordinator = hass.data[DOMAIN][entry.entry_id]
    din = entry.data["din"]

    # Erster Abruf beim Start
    await coordinator.async_config_entry_first_refresh()

    entities = []
    for key, info in MEAS_MAP.items():
        # Entpacken der 5-spaltigen MEAS_MAP
        category, name, multiplier, unit, description = info
        
        entities.append(
            SolarMaxSensor(
                coordinator, 
                din,
                key, 
                name, 
                multiplier, 
                unit, 
                category, 
                description
            )
        )
    async_add_entities(entities)


class SolarMaxSensor(CoordinatorEntity, SensorEntity):
    """Repräsentation eines SolarMax Sensors mit Kategorien und Tooltips."""
    
    _attr_has_entity_name = True

    def __init__(self, coordinator, din, key, name, multiplier, unit, category, description):
        super().__init__(coordinator)
        self._key = key
        self._din = din
        self._multiplier = multiplier
        self._description = description
        
        # HA Attribute
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_entity_category = category
        self._attr_unique_id = f"solarmax_{din}_{key}"

    @property
    def native_value(self):
        """Verarbeitet den Rohwert entsprechend des Typs."""
        v = self.coordinator.data.get(self._key)
        if v is None:
            return None

        # 1. Bitmaske (SAL)
        if self._key == "SAL":
            return translate_bitmask(v, SAL_MAP)

        # 2. Text-Mappings (SYS, TYP)
        if self._key == "SYS":
            return SYS_MAP.get(v, v)
        if self._key == "TYP":
            return TYP_MAP.get(v, v)

        # 3. Statische Strings
        if self._key in ("DIN", "ADR", "SWV", "BDN"):
            return v

        # 4. Numerische Messwerte
        try:
            return round(v * self._multiplier, 2)
        except (TypeError, Exception):
            return v

    @property
    def extra_state_attributes(self):
        """Hinterlegt die Beschreibung als 'Tooltip' in den Attributen."""
        return {
            "beschreibung": self._description,
            "raw_key": self._key
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._din)},
            name=f"SolarMax {self._din}",
            manufacturer="SolarMax",
            model=TYP_MAP.get(self.coordinator.data.get("TYP", 0), "SolarMax"),
            serial_number=str(self._din),
        )
