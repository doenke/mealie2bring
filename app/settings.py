import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    mealie_base_url: str
    mealie_api_token: str
    mealie_shopping_list_id: str
    bring_email: str
    bring_password: str
    bring_list_uuid: Optional[str]
    sync_interval_minutes: int
    log_path: Path
    log_retention_days: int
    port: int
    dashboard_logo_url: Optional[str]
    default_locale: str
    date_formats: Dict[str, str]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        mealie_base_url=os.getenv("MEALIE_BASE_URL", "http://localhost:9000"),
        mealie_api_token=os.getenv("MEALIE_API_TOKEN", ""),
        mealie_shopping_list_id=os.getenv("MEALIE_SHOPPING_LIST_ID", ""),
        bring_email=os.getenv("BRING_EMAIL", ""),
        bring_password=os.getenv("BRING_PASSWORD", ""),
        bring_list_uuid=os.getenv("BRING_LIST_UUID"),
        sync_interval_minutes=_env_int("SYNC_INTERVAL_MINUTES", 3),
        log_path=Path(os.getenv("LOG_PATH", "/data/mealie_bring_sync.log")),
        log_retention_days=_env_int("LOG_RETENTION_DAYS", 30),
        port=_env_int("PORT", 1235),
        dashboard_logo_url=os.getenv("DASHBOARD_LOGO_URL"),
        default_locale=os.getenv("DASHBOARD_LOCALE", "de"),
        date_formats={
            "de": os.getenv("DATE_FORMAT_DE", "%d.%m.%Y %H:%M"),
            "en": os.getenv("DATE_FORMAT_EN", "%Y-%m-%d %H:%M"),
        },
    )
