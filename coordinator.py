# custom_components/solarmax/coordinator.py
# Version 0.0.9

from datetime import timedelta
import logging

import async_timeout

import asyncio
import json
#from homeassistant.components.light import LightEntity
#from homeassistant.core import callback
from homeassistant.core import HomeAssistant
#from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .client import SolarMaxClient
from .protocol import build_read
from .const import DOMAIN, MEAS_MAP

_LOGGER = logging.getLogger(__name__)

# Standard-Intervall für Echtzeitdaten 30
SCAN_INTERVAL = timedelta(seconds=10)

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

class SolarMaxDataCoordinator(DataUpdateCoordinator):
    """Zentraler Manager für kurzlebige Abfrage-Zyklen (YAML-Style)."""

    def __init__(self, hass, address, din, host, port):
        self.host = host
        self.port = port
        self.address = address
        self.din = din
        
        # Wir nutzen ein festes Intervall (z.B. 15 Sek), wie in deiner YAML
        super().__init__(
            hass,
            _LOGGER,
            name=f"SolarMax_{din}",
            update_interval=timedelta(seconds=15),
        )
        _LOGGER.info("!!! COORDINATOR NEU GELADEN 26 !!!")

    def get_safe_batches(self, keys, max_payload=240): # max 
        """Berechnet Batches, um den 242-Byte Puffer des SolarMax nicht zu sprengen."""
        batches = []
        current_batch = []
        current_len = 25 # Start-Offset
        
        for key in keys:
            # Ein Key-Value Paar im Antwort-String braucht ca. 12 Bytes
            estimated_item_len = len(key) + 10 
            if current_len + estimated_item_len > max_payload:
                batches.append(current_batch)
                current_batch = [key]
                current_len = 25 + estimated_item_len
            else:
                current_batch.append(key)
                current_len += estimated_item_len

        _LOGGER.debug("[%s] current_len: %s ", self.din, {estimated_item_len})
        if current_batch:
            batches.append(current_batch)
        return batches

    async def _async_update_data(self):
        #_LOGGER.info("!!! _async_update_data !!!")
        """Erzeugt bei jedem Lauf einen frischen Client und schließt ihn danach."""
        #_LOGGER.debug("[%s] Starte neuen Abfrage-Zyklus an %s", self.din, self.host)
        
        # 1. Client lokal erstellen (Kurzlebigkeit sicherstellen)
        client = SolarMaxClient(self.host, self.port, self.address)
        
        # 2. Das Mega-Telegramm (alle 24 Parameter wie in deinem erfolgreichen Test)
        # Wir nutzen hier direkt dein bewährtes Telegramm
        telegram = "{FB;01;72|64:UDC;IDC;UL1;IL1;PAC;PRL;TNF;KDY;KMT;KYR;KT0;TKK;SYS;KHR;CAC;TYP;SWV;BDN;ADR;PIN;DIN;PLR;PAM;IAA|1DCE}"
        #_LOGGER.debug("[%s] telegram: %s ", self.din, {telegram})

        # # 2. Welche Keys sind JETZT dran?
        #keys_to_query = [k for k, v in MEAS_MAP.items() if v[0] is not None]
        #keys_to_query = [k for k, v in MEAS_MAP.items() if v[0] is None]
        keys_to_query = list(MEAS_MAP.keys()) # Einfach alle Keys nehmen

        #telegram1 = build_read("FB", self.address, keys_to_query)
        #_LOGGER.debug("[%s] telegram: %s ", self.din, {telegram1})
        all_current_data = dict(self.data) if self.data else {}

        await asyncio.sleep(2)
        batches = self.get_safe_batches(keys_to_query)
        num_batches = len(batches)
        _LOGGER.debug("[%s] num_batches: %s ", self.din, {num_batches})
        # for batch in batches:
        #     _LOGGER.debug("[%s] batch: %s", self.din, batch)
        #     telegram = build_read("FB", self.address, batch)
        #     _LOGGER.debug("[%s] telegram: %s ", self.din, {telegram})
        #     resp = await client.send(telegram, timeout=2)
        #     formatted_resp = json.dumps(resp, indent=4)
        #     _LOGGER.debug("[%s] Full Response:\n%s", self.din, formatted_resp)
        #     # if resp and "data" in resp:
        #     #     _LOGGER.debug("[%s] Daten erfolgreich empfangen", self.din)
        #     #     return resp["data"]
        #     if resp and "data" in resp:
        #         # WICHTIG: Wir fügen die neuen Daten dem Bestand hinzu
        #         all_current_data.update(resp["data"])
        #     else:
        #         # Wenn ein Batch leer ist, stimmt was nicht -> Abbruch mit Fehler
        #         raise UpdateFailed(f"Leere Antwort bei Batch {batch}")


        try:
            await asyncio.sleep(1)
            for batch in batches:
                # _LOGGER.debug("[%s] batch: %s", self.din, batch)

                telegram = build_read("FB", self.address, batch)
                #_LOGGER.debug("[%s] telegram1: %s ", self.din, {telegram1})

                # # 3. Senden mit einem gesunden Timeout
                resp = await client.send(telegram, timeout=2)
                #_LOGGER.debug("[%s] resp: %s ", self.din, resp["data"])
                #_LOGGER.debug("[%s] Full Response Object: %s", self.din, resp)
                
                #formatted_resp = json.dumps(resp, indent=4)
                #_LOGGER.debug("[%s] Full Response:\n%s", self.din, formatted_resp)

                # if resp and "data" in resp:
                #     _LOGGER.debug("[%s] Daten erfolgreich empfangen", self.din)
                #     return resp["data"]

                # raise UpdateFailed(f"Inverter {self.din} antwortete mit leerem Paket")
                if resp and "data" in resp:
                    # WICHTIG: Wir fügen die neuen Daten dem Bestand hinzu
                    _LOGGER.debug("[%s] resp: %s ", self.din, resp["data"])
                    all_current_data.update(resp["data"])
                else:
                    # Wenn ein Batch leer ist, stimmt was nicht -> Abbruch mit Fehler
                    raise UpdateFailed(f"Leere Antwort bei Batch {batch}")

        # except Exception as err:
        #     _LOGGER.error("[%s] Kommunikationsfehler (wie bei altem TCP-Sensor): %s", self.din, err)
        #     raise UpdateFailed(f"Verbindung zu {self.host} fehlgeschlagen: {err}")

           # await asyncio.sleep(2)

        except Exception as err:
            _LOGGER.error("[%s] Kommunikationsfehler: %s", self.din, err)
            # Wir nutzen hier eine Standard-Exception, falls UpdateFailed 
            # im Test-Kontext Probleme macht
            raise RuntimeError(f"Verbindung zu {self.host} fehlgeschlagen: {err}")

        finally:
            # 4. "Kill" - Sicherstellen, dass der Socket zu ist und Ressourcen frei werden
            if hasattr(client, 'close'):
                await client.close()
            del client

        return all_current_data
