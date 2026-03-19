from __future__ import annotations

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo
from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    database_url: str
    toteat_base_url: str
    xir: str
    xil: str
    xiu: str
    xapitoken: str
    tenant_id: str = "la-coffeeteria"
    tenant_name: str = "La Coffeeteria"
    db_name: str = "la_coffeeteria"
    timezone_name: str = "America/Santiago"
    locale: str = "es-CL"

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_name)


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql:///la_coffeeteria"),
        toteat_base_url=os.getenv("TOTEAT_BASE_URL", "https://api.toteat.com/mw/or/1.0").rstrip("/"),
        xir=os.environ["TOTEAT_XIR"],
        xil=os.environ["TOTEAT_XIL"],
        xiu=os.environ["TOTEAT_XIU"],
        xapitoken=os.environ.get("TOTEAT_XAPITOKEN") or os.environ["TOTEAT_API_TOKEN"],
    )
