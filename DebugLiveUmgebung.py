# ssh root@<ha-host>
# cd /config
# python3

# Den Code per Copy & Paste in Python 3 einfügen
#######################################
import sys
from unittest.mock import MagicMock

# 1. Wir erstellen eine Liste aller Pfade, die als Pakete erkannt werden müssen
modules_to_mock = [
    "homeassistant",
    "homeassistant.core",
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.exceptions",
    "homeassistant.helpers",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.entity",
    "homeassistant.helpers.entity_platform",
    "voluptuous",
    "async_timeout"
]

# 2. Wir registrieren JEDES Modul einzeln als MagicMock
for mod in modules_to_mock:
    mock = MagicMock()
    # Der Trick: Wir sagen Python, dass dieses Modul ein "Paket" ist
    mock.__path__ = [] 
    sys.modules[mod] = mock

# 3. Jetzt die Basisklasse für den Coordinator einpflanzen
class MockCoordinator:
    def __init__(self, *args, **kwargs):
        self.hass = args[0] if args else None
        self.data = None
        self.update_interval = None
        self.name = "Mock"

sys.modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = MockCoordinator

# 4. Pfad setzen und Import versuchen
import os
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import asyncio
from unittest.mock import MagicMock

#######################################
import logging

# Das hier ist das "Megafon" für deinen Logger:
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
# 2. Den Root-Logger explizit auf DEBUG zwingen
logging.getLogger().setLevel(logging.DEBUG)

_LOGGER = logging.getLogger(__name__)

#################################################
import sys
import importlib

def reload_coordinator():
    """Zwingt Python, die gesamte Kette neu zu lesen."""
    # 1. Alle Module der Integration aus sys.modules werfen
    # Reihenfolge ist hier egal, Hauptsache alle kommen raus
    for mod in [
        'custom_components.solarmax.coordinator',
        'custom_components.solarmax.client',
        'custom_components.solarmax.protocol'
    ]:
        if mod in sys.modules:
            del sys.modules[mod]
    #
    # 2. Jetzt neu importieren (Python liest jetzt alle Dateien frisch)
    global SolarMaxClient
    from custom_components.solarmax.client import SolarMaxClient
    #
    global SolarMaxDataCoordinator
    from custom_components.solarmax.coordinator import SolarMaxDataCoordinator
    #
    # protocol wird implizit durch den Import von client/coordinator neu geladen
    print("--- Komplette Kette (Protocol -> Client -> Coordinator) neu geladen ---")

# 1. Einmal neu laden
# reload_coordinator()

#################################################
SMHOST="<Solarmax-Host-IP>"
SMHSER="<Solarmax-Serial>"

async def test_run():
    coord = SolarMaxDataCoordinator(
        hass=MagicMock(),
        address="01",
        din=SMHSER,
        host=SMHOST,
        port=12345
    )
    #print(f"--- Starte Testlauf für DIN {coord.din} ---")
    try:
        # Hier wird die Methode aufgerufen, die intern self.client.send nutzt
        result = await coord._async_update_data()
        #print(f"Erfolg! Daten: {result}")
    except Exception as e:
        print(f"Fehler im Coordinator-Lauf: {e}")
        import traceback
        traceback.print_exc()
    del coord

async def test_loop():
    print("Starte Stresstest mit Coordinator... Beenden mit Strg+C")
    try:
        while True:
            reload_coordinator()
            await test_run()
    except KeyboardInterrupt:
        print("\nTest durch Benutzer beendet.")

asyncio.run(test_loop())

