from typing import Any, Dict, Optional


TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "de": {
        "dashboard.title": "Mealie → Bring",
        "dashboard.subtitle.sync_disabled": "Automatischer Abruf deaktiviert",
        "dashboard.subtitle.sync_interval": "Abruf alle {minutes} Minuten",
        "dashboard.last_run": "Letzter Lauf",
        "dashboard.last_run.none": "Noch kein Lauf",
        "dashboard.page_generated": "Seite erstellt",
        "dashboard.manual_trigger": "Manuell starten",
        "dashboard.log_title": "Log",
        "dashboard.log_subtitle": "Letzte 30 Tage (max).",
        "dashboard.table.time": "Zeit",
        "dashboard.table.item": "Artikel",
        "dashboard.table.quantity": "Menge",
        "dashboard.table.unit": "Einheit",
        "dashboard.table.bring": "Bring",
        "dashboard.table.mealie": "Mealie",
        "dashboard.table.empty": "Noch keine Einträge",
        "dashboard.footer.project_by": "Ein Projekt von",
        "dashboard.footer.github": "GitHub",
        "dashboard.status.ok": "übernommen",
        "dashboard.mealie.done": "erledigt",
        "dashboard.notice.starting": "Manueller Sync wird gestartet …",
        "dashboard.notice.started": "Sync angestoßen. Ergebnisse folgen im Log.",
        "dashboard.notice.failed": "Sync konnte nicht gestartet werden. Bitte erneut versuchen.",
        "log.sync_started": "Sync gestartet",
        "log.mealie_config_missing": "Mealie Konfiguration fehlt",
        "log.mealie_fetch_failed": "Fehler beim Abrufen der Mealie-Liste",
        "log.mealie_no_items": "Keine Items in der Mealie-Liste gefunden",
        "log.mealie_no_open_items": "Keine offenen Items - Bring wird nicht kontaktiert",
        "log.item_missing_name": "Item ohne Namen übersprungen",
        "log.mealie_mark_done": "In Mealie als erledigt markiert",
        "log.mealie_mark_failed": "Konnte in Mealie nicht abhaken",
        "log.bring_credentials_missing": "Bring Zugangsdaten fehlen",
        "log.bring_login_failed": "Bring Login fehlgeschlagen",
        "log.bring_login_incomplete": "Bring Login Antwort unvollständig",
        "log.bring_item_transferred": "An Bring übertragen",
        "log.bring_item_failed": "Bring-Übertragung fehlgeschlagen",
    },
    "en": {
        "dashboard.title": "Mealie → Bring",
        "dashboard.subtitle.sync_disabled": "Automatic sync disabled",
        "dashboard.subtitle.sync_interval": "Sync every {minutes} minutes",
        "dashboard.last_run": "Last run",
        "dashboard.last_run.none": "No runs yet",
        "dashboard.page_generated": "Page generated",
        "dashboard.manual_trigger": "Start manually",
        "dashboard.log_title": "Log",
        "dashboard.log_subtitle": "Last 30 days (max).",
        "dashboard.table.time": "Time",
        "dashboard.table.item": "Item",
        "dashboard.table.quantity": "Quantity",
        "dashboard.table.unit": "Unit",
        "dashboard.table.bring": "Bring",
        "dashboard.table.mealie": "Mealie",
        "dashboard.table.empty": "No entries yet",
        "dashboard.footer.project_by": "A project by",
        "dashboard.footer.github": "GitHub",
        "dashboard.status.ok": "transferred",
        "dashboard.mealie.done": "done",
        "dashboard.notice.starting": "Manual sync is starting …",
        "dashboard.notice.started": "Sync started. Results will appear in the log.",
        "dashboard.notice.failed": "Sync could not be started. Please try again.",
        "log.sync_started": "Sync started",
        "log.mealie_config_missing": "Mealie configuration missing",
        "log.mealie_fetch_failed": "Failed to fetch Mealie list",
        "log.mealie_no_items": "No items found in the Mealie list",
        "log.mealie_no_open_items": "No open items - Bring will not be contacted",
        "log.item_missing_name": "Skipped item without a name",
        "log.mealie_mark_done": "Marked as done in Mealie",
        "log.mealie_mark_failed": "Could not mark as done in Mealie",
        "log.bring_credentials_missing": "Bring credentials are missing",
        "log.bring_login_failed": "Bring login failed",
        "log.bring_login_incomplete": "Bring login response incomplete",
        "log.bring_item_transferred": "Transferred to Bring",
        "log.bring_item_failed": "Bring transfer failed",
    },
}


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def translate(
    message_key: str,
    context: Optional[Dict[str, Any]] = None,
    locale: str = "de",
    fallback_locale: str = "de",
) -> str:
    translations = TRANSLATIONS.get(locale)
    if translations is None:
        base_locale = locale.split("-")[0]
        translations = TRANSLATIONS.get(base_locale)
    if translations is None:
        translations = TRANSLATIONS.get(fallback_locale, {})
    message = translations.get(message_key, message_key)
    return message.format_map(_SafeDict(context or {}))
