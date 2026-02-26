# custom_components/solarmax/client.py
# Version 0.0.8

from __future__ import annotations
import asyncio
from .protocol import parse_response

class SolarMaxClient:
    def __init__(self, host: str, port: int, address: str):
        self.host = host
        self.port = port
        self.address = address

    async def send(self, telegram: str, timeout: float = 5.0) -> dict:
        reader, writer = await asyncio.open_connection(self.host, self.port)
        try:
            writer.write(telegram.encode("ascii"))
            await writer.drain()
            raw = await asyncio.wait_for(reader.readuntil(b"}"), timeout)
            text = raw.decode("ascii", errors="replace")
            start = text.find("{")
            end = text.find("}", start + 1)
            if start != -1 and end != -1:
                frame = text[start : end + 1]
                return parse_response(frame)
            return {}
        finally:
            # writer.close()
            # try:
            #     await writer.wait_closed()
            # except Exception:
            #     pass
            if 'writer' in locals() and writer:
                writer.close()
                try:
                    # Das ist das Wichtigste: Warten, bis der Port wirklich ZU ist
                    await asyncio.wait_for(writer.wait_closed(), timeout=2.0)
                except:
                    pass
