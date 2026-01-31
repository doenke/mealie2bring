from typing import Any, Dict

LOG_MESSAGE_CATALOG = {
    "log.sync_started": "Sync gestartet",
    "log.mealie_config_missing": "Mealie Konfiguration fehlt",
    "log.mealie_fetch_failed": "Fehler beim Abrufen der Mealie-Liste",
    "log.mealie_no_items": "Keine Items in der Mealie-Liste gefunden",
    "log.mealie_no_open_items": "Keine offenen Items - Bring wird nicht kontaktiert",
    "log.bring_credentials_missing": "Bring Zugangsdaten fehlen",
    "log.bring_login_failed": "Bring Login fehlgeschlagen",
    "log.bring_login_response_incomplete": "Bring Login Antwort unvollständig",
    "log.item_missing_name": "Item ohne Namen übersprungen",
    "log.mealie_marked_done": "In Mealie als erledigt markiert",
    "log.mealie_mark_failed": "Konnte in Mealie nicht abhaken",
    "log.bring_transfer_success": "An Bring übertragen",
    "log.bring_transfer_failed": "Bring-Übertragung fehlgeschlagen",
}


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def t(message_key: str, context: Dict[str, Any] | None = None) -> str:
    template = LOG_MESSAGE_CATALOG.get(message_key, message_key)
    if not context:
        return template
    return template.format_map(_SafeFormatDict(context))


def translate_log_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    if entry.get("type") != "event":
        return entry
    message_key = entry.get("message_key")
    if not message_key:
        return entry
    translated = dict(entry)
    translated["message"] = t(message_key, translated.get("context") or {})
    return translated
