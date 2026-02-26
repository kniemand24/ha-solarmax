# custom_components/solarmax/const.py
# Version 0.0.8

from __future__ import annotations

DOMAIN = "solarmax"
PLATFORMS = ["sensor", "number", "button"] # Sensors, Controls="number", "button"

DEFAULT_PORT = 12345
DEFAULT_ADDRESS = "01"

FULL_KEYS = (
    "UDC;IDC;UL1;IL1;PAC;PRL;TNF;KDY;KMT;KYR;KT0;TKK;SYS;KHR;CAC;TYP;SWV;BDN;ADR;PIN;DIN;PLR;PAM;IAA"
).split(";")

# Betriebsmodus (SYS) – Beispiele
# Werte sind DECIMAL (wir konvertieren aus HEX zu int im Parser)
SYS_MAP: dict[int, str] = {
    20000: "Keine Kommunikation",
    20001: "In Betrieb",
    20002: "Wenig Einstrahlung",
    20003: "Anfahren",
    20004: "Betrieb bei MPP",
    20005: "Ventilator läuft",
    20006: "Betrieb auf Maximalleistung",
    20007: "Temperaturbegrenzung",
    20008: "Netzbetrieb",
    20106: "Isolationsfehler",
    20107: "Fehler Netzrelais",
    20115: "Kein Netz",
}

# Gerätetyp (TYP) – gängige S‑Serie
TYP_MAP: dict[int, str] = {
    20010: "SOLARMAX 2000S",
    20020: "SOLARMAX 3000S",
    20030: "SOLARMAX 4200S",
    20040: "SOLARMAX 6000S",
}

# Geräte Alarm Codes (SAL) - Bit-Werte
SAL_MAP: dict[int, str] = {
    0: "kein Fehler",
    1: "Externer Fehler 1",
    2: "Isolationsfehler DC-Seite",
    4: "Fehlerstrom Erde zu Groß",
    8: "Sicherungsbruch Mittelpunkterde",
    16: "Externer Alarm 2",
    32: "Langzeit-Temperaturbegrenzung",
    64: "Fehler AC-Einspeisung",
    128: "Externer Alarm 4",
    256: "Ventilator defekt",
    512: "Sicherungsbruch",
    1024: "Ausfall Temperatursensor",
    2048: "Alarm 12",
    4096: "Alarm 13",
    8192: "Alarm 14",
    16384: "Alarm 15",
    32768: "Alarm 16",
    65536: "Alarm 17",
}

# Hilfsfunktion, um Bit-Werte zusammenzufassen.
def translate_bitmask(value, mapping):
    """Zerlegt eine Bitmaske in eine Liste von Texten."""
    if value == 0:
        return mapping.get(0, "Kein Fehler")
    
    # In C++: vector<string> results;
    results = [
        text for code, text in mapping.items() 
        if code != 0 and (value & code) == code
    ]
    
    # Wenn wir Bits gefunden haben, fügen wir sie zusammen, 
    # andernfalls geben wir den Rohwert zurück
    return ", ".join(results) if results else str(value)

# Typabhängige Einstellbereiche (Nutzerwerte!)
# - PLR/IAA in %
# - PAM/PIN in Watt (echte Watt)
# Angaben für 3000S/4200S gemäß deinen Tests; weitere Typen nutzen DEFAULT_RANGES.
TYPE_RANGES: dict[int, dict[str, tuple[int, int]]] = {
    # SOLARMAX 3000S
    20020: {
        "PAM": (1400, 2750),
        "PIN": (2100, 10000),
        "PLR": (0, 100),
        "IAA": (5, 100),
    },
    # SOLARMAX 4200S
    20030: {
        "PAM": (2100, 4180),
        "PIN": (2100, 10000),
        "PLR": (0, 100),
        "IAA": (5, 100),
    },
}

# Konservative Defaults (für weitere Typen z. B. 2000S), bis genauere Werte vorliegen
DEFAULT_RANGES: dict[str, tuple[int, int]] = {
    "PAM": (1000, 6000),   # echte Watt
    "PIN": (0, 10000),     # echte Watt
    "PLR": (0, 100),       # %
    "IAA": (5, 100),       # %
}

## Definition aller Sensoren
MEAS_MAP = {
    "UDC": ("DC Voltage", 0.1, "V"),
    "IDC": ("DC Current", 0.01, "A"),
    "UL1": ("AC Voltage", 0.1, "V"),
    "IL1": ("AC Current", 0.01, "A"),
    "PAC": ("AC Power", 0.5, "W"),
    "PRL": ("Power Relative", 1, "%"),
    "TNF": ("Frequency", 0.01, "Hz"),
    "KDY": ("Energy Today", 0.1, "kWh"),
    "KMT": ("Energy Month", 1, "kWh"),
    "KYR": ("Energy Year", 1, "kWh"),
    "KT0": ("Energy Total", 1, "kWh"),
    "TKK": ("Temperature", 1, "°C"),
    "SYS": ("Operating Mode", 1, None),
    "KHR": ("Operating Hours", 1, "h"),
    "CAC": ("Start-ups", 1, None),
    "TYP": ("Type", 1, None),
    "SWV": ("Software Version", 0.1, None),
    "BDN": ("Build Number", 1, None),
    "ADR": ("Network Address", 1, None),
    "PIN": ("Installed Capacity", 0.5, "W"),  # 0 - 5000 W
    "DIN": ("Serial Number", 1, None),
    "PLR": ("Power Limit", 1, "%"),
    "PAM": ("AC Output MAX", 0.5, "W"),
    "IAA": ("AC Output MAX IAA", 1, "%"),
    "ILM": ("AC Output MAX ILM", 0.01, "A"),  # 10 - 19 A
    # Fehlerstrom
    "IEE": ("Ierr", 0.1, "mA"),
    "IEA": ("Ierr AC", 0.1, "mA"), 
    "IED": ("Ierr DC", 0.1, "mA"),
    "IEM": ("Ierr max", 0.1, "mA"),           # Fehlerstrom Max  50 - 300 mA
    # cos(phi)
    "COS": ("cos(phi)", 1, None),
    # Fehler
    "EC00": ("Fehler 0", 1, None),
    "EC01": ("Fehler 1", 1, None),
    "EC02": ("Fehler 2", 1, None),
    "EC03": ("Fehler 3", 1, None),
    "EC04": ("Fehler 4", 1, None),
    "EC05": ("Fehler 5", 1, None),
    "EC06": ("Fehler 6", 1, None),
    "EC07": ("Fehler 7", 1, None),
    # Alarm Codes
    "SAL": ("Alarm Codes", 1, None),
}


from homeassistant.helpers.entity import EntityCategory

# Hilfskonstanten zur einfacheren Zuordnung
CAT_NONE = None
CAT_DIAG = EntityCategory.DIAGNOSTIC
CAT_CONF = EntityCategory.CONFIG

MEAS_MAP = {
    # --- Echtzeit-Messwerte (Standard-Sensoren) ---
    "PAC": (CAT_NONE, "AC Leistung", 0.5, "W", "Aktuelle Wirkleistung, die in das Hausnetz eingespeist wird."),
    "UDC": (CAT_NONE, "DC Spannung", 0.1, "V", "Aktuelle Eingangsspannung der PV-Module (String-Spannung)."),
    "IDC": (CAT_NONE, "DC Strom", 0.01, "A", "Aktueller Eingangsstrom der PV-Module."),
    "UL1": (CAT_NONE, "AC Spannung", 0.1, "V", "Netzspannung auf der Ausgangsseite (Phase 1)."),
    "IL1": (CAT_NONE, "AC Strom", 0.01, "A", "Ausgangsstrom auf der Netzseite (Phase 1)."),
    "TNF": (CAT_NONE, "Netzfrequenz", 0.01, "Hz", "Aktuelle Frequenz des öffentlichen Stromnetzes."),
    "PRL": (CAT_NONE, "Relative Leistung", 1, "%", "Aktuelle Auslastung des Wechselrichters in Prozent zur Nennleistung."),
    "TKK": (CAT_NONE, "Temperatur Kühlkörper", 1, "°C", "Innentemperatur des Wechselrichters am Kühlkörper."),
    "SYS": (CAT_NONE, "Betriebszustand", 1, None, "Aktueller Status (z.B. Standby, Einspeisen, Warten auf Sonne)."),

    # --- Energie & Statistik (Standard-Sensoren) ---
    "KDY": (CAT_NONE, "Energie Heute", 0.1, "kWh", "Ertrag des aktuellen Tages."),
    "KMT": (CAT_NONE, "Energie Monat", 1, "kWh", "Gesamtertrag des aktuellen Monats."),
    "KYR": (CAT_NONE, "Energie Jahr", 1, "kWh", "Gesamtertrag des laufenden Kalenderjahres."),
    "KT0": (CAT_NONE, "Energie Gesamt", 1, "kWh", "Gesamtlebensdauer-Ertrag des Wechselrichters."),
    "KHR": (CAT_NONE, "Betriebsstunden", 1, "h", "Gesamtzahl der Stunden, die das Gerät in Betrieb war."),
    "CAC": (CAT_NONE, "Starts", 1, None, "Anzahl der Netzaufschaltungen (Relais-Schaltungen)."),

    # --- Fehlerstrom-Messungen (Diagnose) ---
    "IEE": (CAT_DIAG, "Fehlerstrom Ierr", 0.1, "mA", "Aktueller Differenzstrom (Leckstrom) der Anlage."),
    "IEA": (CAT_DIAG, "Ierr AC", 0.1, "mA", "AC-Anteil des Fehlerstroms."),
    "IED": (CAT_DIAG, "Ierr DC", 0.1, "mA", "DC-Anteil des Fehlerstroms."),
    "IEM": (CAT_DIAG, "Ierr Max", 0.1, "mA", "Maximal zulässiger Fehlerstrom vor Sicherheitsabschaltung."),

    # --- Konfiguration & Limits (Konfiguration) ---
    "PAM": (CAT_DIAG, "Max. AC Leistung", 0.5, "W", "Maximalwert der Wirkleistung (Begrenzung am WR)."),
    "PLR": (CAT_NONE, "Leistungsbegrenzung", 1, "%", "Aktuell eingestellte relative Begrenzung der Ausgangsleistung."),
    "PIN": (CAT_DIAG, "Installierte Leistung", 0.5, "W", "Konfigurierte DC-Nennleistung der angeschlossenen Module."),
    "COS": (CAT_DIAG, "cos(phi)", 0.01, None, "Aktueller Verschiebungsfaktor der Blindleistungseinstellung."),
    "IAA": (CAT_NONE, "Max. Strom IAA", 1, "%", "Maximaler Ausgangsstrom in Prozent."),
    "ILM": (CAT_DIAG, "Max. Strom ILM", 0.01, "A", "Absolutes Stromlimit auf der AC-Seite."),

    # --- Geräteinformationen & Historie (Diagnose) ---
    "TYP": (CAT_DIAG, "Gerätetyp", 1, None, "Modellkennung des SolarMax Wechselrichters."),
    "DIN": (CAT_DIAG, "Seriennummer", 1, None, "Eindeutige Seriennummer des Geräts."),
    "SWV": (CAT_DIAG, "Software Version", 0.1, None, "Version der Firmware auf dem Kommunikationsboard."),
    "BDN": (CAT_DIAG, "Build Nummer", 1, None, "Detaillierte Build-Nummer der Firmware."),
    "ADR": (CAT_DIAG, "Netzwerkadresse", 1, None, "Eingestellte RS485/Bus-Adresse des Geräts."),
    "SAL": (CAT_DIAG, "Alarm Codes", 1, None, "Aktuelle Fehler-Bitmaske (SAL)."),
    "EC00": (CAT_DIAG, "Fehler 0", 1, None, "Letzter Eintrag in der Fehlerhistorie."),
    "EC01": (CAT_DIAG, "Fehler 1", 1, None, "Vorletzter Eintrag in der Fehlerhistorie."),
    "EC02": (CAT_DIAG, "Fehler 2", 1, None, "Drittletzter Eintrag in der Fehlerhistorie."),
    "EC03": (CAT_DIAG, "Fehler 3", 1, None, "Eintrag 4 in der Fehlerhistorie."),
    "EC04": (CAT_DIAG, "Fehler 4", 1, None, "Eintrag 5 in der Fehlerhistorie."),
    "EC05": (CAT_DIAG, "Fehler 5", 1, None, "Eintrag 6 in der Fehlerhistorie."),
    "EC06": (CAT_DIAG, "Fehler 6", 1, None, "Eintrag 7 in der Fehlerhistorie."),
    "EC07": (CAT_DIAG, "Fehler 7", 1, None, "Eintrag 8 in der Fehlerhistorie."),
}
