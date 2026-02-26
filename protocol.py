# custom_components/solarmax/protocol.py
# Version 0.0.7 – ACK-Parsing robuster (OK/KO case-insensitiv, trim CR/Whitespace/';')
from __future__ import annotations

FRS, FS, US = "|", ";", ":"
PORT_READ = "64"   # 100 dez – Nutzdaten lesen
PORT_WRITE = "C8"  # 200 dez – Einstellungen/Befehle
LENGTH_OFFSET = 16  # empirisch bestätigt (dein Dialekt)

def _crc_ascii16(s: str) -> str:
    return f"{(sum(ord(c) for c in s) & 0xFFFF):04X}"

def build_read(src: str, dest: str, keys: list[str]) -> str:
    data_str = f"{PORT_READ}:{';'.join(keys)}"
    len_hex = f"{len(data_str) + LENGTH_OFFSET:02X}"
    payload_wo_crc = f"{src}{FS}{dest}{FS}{len_hex}{FRS}{data_str}{FRS}"
    crc = _crc_ascii16(payload_wo_crc)
    return "{" + payload_wo_crc + crc + "}"

def build_write(src: str, dest: str, assignment: str) -> str:
    # assignment z.B. "PLR=4D" (HEX), "PAM=157C" (HEX)
    data_str = f"{PORT_WRITE}:{assignment}"
    len_hex = f"{len(data_str) + LENGTH_OFFSET:02X}"
    payload_wo_crc = f"{src}{FS}{dest}{FS}{len_hex}{FRS}{data_str}{FRS}"
    crc = _crc_ascii16(payload_wo_crc)
    return "{" + payload_wo_crc + crc + "}"

def parse_response(frame: str) -> dict:
    t = frame.strip()
    if not t or t[0] != "{" or t[-1] not in ("}", ")"):
        return {}
    try:
        inner = t[1:-1]
        header, data_union, crc = inner.split(FRS)
        dest, src, len_hex = header.split(FS)
        port, payload = (data_union.split(US, 1) + [""])[:2]

        vals: dict[str, int | str] = {}
        ack: str | None = None

        if payload:
            for item in [p for p in payload.split(FS) if p]:
                if "=" in item:
                    k, v = item.split("=", 1)
                    if "," in v:
                        v = v.split(",", 1)[0]
                    try:
                        vals[k] = int(v, 16)
                    except ValueError:
                        vals[k] = v
                else:
                    # ACK robust (OK/KO, trim CR/Whitespace/';')
                    tok = item.strip().strip("\r").strip(";")
                    upper = tok.upper()
                    if upper in ("OK", "KO"):
                        ack = "Ok" if upper == "OK" else "Ko"
        return {
            "src": src,
            "dest": dest,
            "len": len_hex,
            "port": port,
            "data": vals,
            "ack": ack,
            "crc": crc,
            "raw": t,
        }
    except Exception:
        return {}
