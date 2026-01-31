import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from .settings import Settings, get_settings

logger = logging.getLogger("mealie2bring")

SYNC_LOCK = asyncio.Lock()


@dataclass
class BringAuth:
    token: str
    user_uuid: str
    list_uuid: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_quantity(value: Optional[float]) -> str:
    if value is None:
        return ""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric == 0:
        return ""
    if numeric.is_integer():
        return str(int(numeric))
    return str(numeric)


def _build_note(quantity: Optional[float], unit: Optional[str]) -> str:
    parts = [part for part in [_format_quantity(quantity), unit or ""] if part]
    return " ".join(parts).strip()


def _log_entry_path(settings: Settings) -> Path:
    path = Path(settings.log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _append_log_entry(settings: Settings, entry: Dict[str, Any]) -> None:
    path = _log_entry_path(settings)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _prune_log_entries(settings: Settings) -> List[Dict[str, Any]]:
    path = Path(settings.log_path)
    if not path.exists():
        return []

    cutoff = _now() - timedelta(days=settings.log_retention_days)
    retained: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        timestamp = entry.get("timestamp")
        if not timestamp:
            continue
        try:
            parsed = datetime.fromisoformat(timestamp)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        if parsed >= cutoff:
            retained.append(entry)

    path.write_text("\n".join(json.dumps(entry, ensure_ascii=False) for entry in retained) + ("\n" if retained else ""), encoding="utf-8")
    return retained


def load_log_entries(settings: Settings) -> List[Dict[str, Any]]:
    entries = _prune_log_entries(settings)
    filtered = [
        entry
        for entry in entries
        if not (entry.get("type") == "item" and entry.get("status") == "skipped")
    ]
    return sorted(filtered, key=lambda entry: entry.get("timestamp", ""), reverse=True)


def _log_event(settings: Settings, level: str, message_key: str, context: Optional[Dict[str, Any]] = None) -> None:
    entry = {
        "timestamp": _now().isoformat(),
        "level": level,
        "type": "event",
        "message_key": message_key,
        "context": context or {},
    }
    _append_log_entry(settings, entry)
    logger.log(getattr(logging, level, logging.INFO), "%s | %s", message_key, context or {})


def _log_item(settings: Settings, payload: Dict[str, Any]) -> None:
    entry = {
        "timestamp": _now().isoformat(),
        "type": "item",
        **payload,
    }
    _append_log_entry(settings, entry)
    logger.info("%s | %s", payload.get("status"), {"name": payload.get("name"), "note": payload.get("note")})


async def _fetch_mealie_list(settings: Settings) -> List[Dict[str, Any]]:
    url = f"{settings.mealie_base_url.rstrip('/')}/api/households/shopping/lists/{settings.mealie_shopping_list_id}"
    headers = {
        "Authorization": f"Bearer {settings.mealie_api_token}",
        "Accept": "application/json",
    }
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                body = await response.text()
                _log_event(settings, "ERROR", "log.mealie_fetch_failed", {
                    "status": response.status,
                    "body": body,
                })
                return []
            data = await response.json()
            return data.get("listItems", [])


async def _bring_login(settings: Settings) -> Optional[BringAuth]:
    if not settings.bring_email or not settings.bring_password:
        _log_event(settings, "ERROR", "log.bring_credentials_missing")
        return None

    url = "https://api.getbring.com/rest/v2/bringauth"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-BRING-API-KEY": "webApp",
        "X-BRING-CLIENT": "webApp",
        "X-BRING-CLIENT-VERSION": "1.0.0",
        "User-Agent": "BringWebApp/1.0",
    }
    payload = {
        "email": settings.bring_email,
        "password": settings.bring_password,
    }
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, data=payload, headers=headers) as response:
            if response.status != 200:
                body = await response.text()
                _log_event(settings, "ERROR", "log.bring_login_failed", {
                    "status": response.status,
                    "body": body,
                })
                return None
            data = await response.json()

    token = data.get("access_token")
    user_uuid = data.get("uuid")
    list_uuid = settings.bring_list_uuid or data.get("bringListUUID")
    if not token or not user_uuid or not list_uuid:
        _log_event(settings, "ERROR", "log.bring_login_incomplete", data)
        return None

    return BringAuth(token=token, user_uuid=user_uuid, list_uuid=list_uuid)


async def _bring_add_item(auth: BringAuth, name: str, note: str) -> bool:
    url = f"https://api.getbring.com/rest/v2/bringlists/{auth.list_uuid}"
    headers = {
        "Authorization": f"Bearer {auth.token}",
        "X-BRING-USER-UUID": auth.user_uuid,
        "X-BRING-API-KEY": "webApp",
        "X-BRING-CLIENT": "webApp",
        "X-BRING-CLIENT-VERSION": "1.0.0",
        "User-Agent": "BringWebApp/1.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "purchase": name,
        "recently": "",
        "specification": note,
    }

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.put(url, data=payload, headers=headers) as response:
            return response.status in {200, 204}


async def _mealie_mark_done(settings: Settings, item: Dict[str, Any]) -> bool:
    url = f"{settings.mealie_base_url.rstrip('/')}/api/households/shopping/items"
    headers = {
        "Authorization": f"Bearer {settings.mealie_api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload_item = dict(item)
    payload_item["checked"] = True
    payload = json.dumps([payload_item])

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.put(url, data=payload, headers=headers) as response:
            return response.status == 200


def _extract_item_details(item: Dict[str, Any]) -> Tuple[Optional[str], str, Optional[str], str, Optional[str]]:
    item_id = item.get("id")
    name = None
    food = item.get("food") or {}
    if isinstance(food, dict):
        name = food.get("name")
    if not name:
        name = item.get("note")
    quantity_value = item.get("quantity")
    quantity = _format_quantity(quantity_value)
    unit = None
    unit_data = item.get("unit") or {}
    if isinstance(unit_data, dict):
        unit = unit_data.get("name")
    note = _build_note(quantity_value, unit)
    return name, note, item_id, quantity, unit


async def sync_mealie_to_bring(trigger: str = "scheduler") -> List[Dict[str, Any]]:
    settings = get_settings()
    async with SYNC_LOCK:
        _prune_log_entries(settings)
        _log_event(settings, "INFO", "log.sync_started", {"trigger": trigger})

        if not settings.mealie_api_token or not settings.mealie_shopping_list_id:
            _log_event(settings, "ERROR", "log.mealie_config_missing")
            return []

        items = await _fetch_mealie_list(settings)
        if not items:
            _log_event(settings, "INFO", "log.mealie_no_items")
            return []

        open_items = [item for item in items if not item.get("checked")]
        if not open_items:
            _log_event(settings, "INFO", "log.mealie_no_open_items")
            return []

        auth = await _bring_login(settings)
        if not auth:
            return []

        results: List[Dict[str, Any]] = []
        for item in items:
            if item.get("checked"):
                continue

            name, note, item_id, quantity, unit = _extract_item_details(item)
            if not name:
                _log_event(settings, "WARN", "log.item_missing_name", {"itemId": item_id})
                continue

            ok = await _bring_add_item(auth, name, note)
            status = "ok" if ok else "error"

            mealie_state = "-"
            if ok and item_id:
                done = await _mealie_mark_done(settings, item)
                mealie_state = "done" if done else "open"
                if done:
                    _log_event(settings, "INFO", "log.mealie_mark_done", {
                        "itemId": item_id,
                        "name": name,
                    })
                else:
                    _log_event(settings, "WARN", "log.mealie_mark_failed", {
                        "itemId": item_id,
                        "name": name,
                    })
            elif ok:
                mealie_state = "skipped"

            if ok:
                _log_event(settings, "INFO", "log.bring_item_transferred", {
                    "itemId": item_id,
                    "name": name,
                    "note": note,
                })
            else:
                _log_event(settings, "ERROR", "log.bring_item_failed", {
                    "itemId": item_id,
                    "name": name,
                })

            payload = {
                "status": status,
                "name": name,
                "note": note,
                "quantity": quantity,
                "unit": unit,
                "mealie": mealie_state,
                "itemId": item_id,
            }
            _log_item(settings, payload)
            results.append(payload)

        return results
