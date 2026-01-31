import html
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .i18n import translate
from .scheduler import create_scheduler
from .settings import Settings, get_settings
from .sync import load_log_entries, sync_mealie_to_bring

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="Mealie → Bring Sync")
app.state.scheduler = create_scheduler()

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def _pick_supported_locale(value: str, settings: Settings) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower().replace("_", "-")
    if normalized in settings.date_formats:
        return normalized
    base = normalized.split("-")[0]
    if base in settings.date_formats:
        return base
    return None


def _resolve_locale(request: Request, settings: Settings) -> str:
    if settings.ui_locale:
        resolved = _pick_supported_locale(settings.ui_locale, settings)
        if resolved:
            return resolved
    header = request.headers.get("accept-language", "")
    for part in header.split(","):
        lang = part.split(";")[0]
        resolved = _pick_supported_locale(lang, settings)
        if resolved:
            return resolved
    resolved_default = _pick_supported_locale(settings.default_locale, settings)
    if resolved_default:
        return resolved_default
    return next(iter(settings.date_formats), "de")


def _format_timestamp(value: str, settings: Settings, locale: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    localized = parsed.astimezone()
    format_string = settings.date_formats.get(locale)
    if not format_string:
        base_locale = locale.split("-")[0]
        format_string = settings.date_formats.get(base_locale)
    if not format_string:
        format_string = settings.date_formats.get(settings.default_locale, "%d.%m.%Y %H:%M")
    return localized.strftime(format_string)


def _format_now(settings: Settings, locale: str) -> str:
    return _format_timestamp(datetime.now(timezone.utc).isoformat(), settings, locale)


def _escape_html(value: str | None) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _translate_event(entry: dict, locale: str, settings: Settings) -> None:
    if entry.get("type") != "event":
        return
    message_key = entry.get("message_key")
    if not message_key:
        return
    entry["message"] = translate(
        message_key,
        entry.get("context", {}),
        locale=locale,
        fallback_locale=settings.fallback_locale,
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    settings = get_settings()
    locale = _resolve_locale(request, settings)

    def t(message_key: str, context: dict | None = None) -> str:
        return translate(
            message_key,
            context or {},
            locale=locale,
            fallback_locale=settings.fallback_locale,
        )

    entries = load_log_entries(settings)
    for entry in entries:
        _translate_event(entry, locale, settings)
    last_sync_entry = next(
        (
            entry
            for entry in entries
            if entry.get("type") == "event" and entry.get("message_key") == "log.sync_started"
        ),
        None,
    )
    last_sync_display = (
        _format_timestamp(last_sync_entry.get("timestamp", ""), settings, locale)
        if last_sync_entry
        else t("dashboard.last_run.none")
    )
    page_generated = _format_now(settings, locale)
    custom_logo_html = ""
    if settings.dashboard_logo_url:
        escaped_logo_url = _escape_html(settings.dashboard_logo_url)
        custom_logo_html = (
            f'<div class="logo logo--custom actions-logo"><img src="{escaped_logo_url}" alt="Logo" /></div>'
        )
    manual_trigger_label = _escape_html(t("dashboard.manual_trigger"))
    logo_html = (
        '<div class="logo-stack">'
        '<div class="logo logo--generated">'
        '<img src="/static/Mealie2Bring.png" alt="Mealie + Bring Logo" />'
        "</div>"
        "</div>"
    )
    actions_row_html = (
        '<div class="actions-row">'
        f"{custom_logo_html}"
        f'<button type="button" id="manual-trigger">{manual_trigger_label}</button>'
        "</div>"
    )
    status_labels = {
        "ok": t("dashboard.status.ok"),
    }
    mealie_labels = {
        "done": t("dashboard.mealie.done"),
    }
    rows = []
    for entry in entries:
        if entry.get("type") != "item":
            continue
        status_value_raw = entry.get("status", "")
        status_label_raw = status_labels.get(status_value_raw, status_value_raw)
        mealie_value_raw = entry.get("mealie", "-")
        mealie_label_raw = mealie_labels.get(mealie_value_raw, mealie_value_raw)
        status_value = _escape_html(status_value_raw)
        status_label = _escape_html(status_label_raw)
        mealie_value = _escape_html(mealie_value_raw)
        mealie_label = _escape_html(mealie_label_raw)
        mealie_class = (
            f" class='{mealie_value}'" if mealie_value_raw and mealie_value_raw != "-" else ""
        )
        rows.append(
            f"<tr>"
            f"<td>{_escape_html(_format_timestamp(entry.get('timestamp',''), settings, locale))}</td>"
            f"<td>{_escape_html(entry.get('name',''))}</td>"
            f"<td>{_escape_html(entry.get('quantity') or '')}</td>"
            f"<td>{_escape_html(entry.get('unit') or '')}</td>"
            f"<td class='{status_value}'>{status_label}</td>"
            f"<td{mealie_class}>{mealie_label}</td>"
            f"</tr>"
        )

    sync_label = (
        t("dashboard.subtitle.sync_disabled")
        if settings.sync_interval_minutes <= 0
        else t("dashboard.subtitle.sync_interval", {"minutes": settings.sync_interval_minutes})
    )
    translations = {
        "noticeStarting": t("dashboard.notice.starting"),
        "noticeStarted": t("dashboard.notice.started"),
        "noticeFailed": t("dashboard.notice.failed"),
    }
    translations_json = json.dumps(translations)
    html = f"""
    <!DOCTYPE html>
    <html lang="{_escape_html(locale)}">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{_escape_html(t("dashboard.title"))}</title>
        <link rel="stylesheet" href="/static/style.css" />
        <link rel="icon" type="image/png" href="/static/Mealie2Bring.png" />
      </head>
      <body>
        <main class="container">
          <header class="header">
            <div class="header-title">
              {logo_html}
              <div>
              <h1 class="title-eyebrow">{_escape_html(t("dashboard.title"))}</h1>
              <p class="subtitle">{_escape_html(sync_label)}</p>
              <div class="status-meta">
                <p class="meta-line">{_escape_html(t("dashboard.last_run"))}: {_escape_html(last_sync_display)}</p>
                <p class="meta-line">{_escape_html(t("dashboard.page_generated"))}: {_escape_html(page_generated)}</p>
              </div>
              </div>
            </div>
            <div class="actions">
              {actions_row_html}
              <p id="trigger-notice" class="notification" role="status" aria-live="polite"></p>
            </div>
          </header>

          <section class="panel">
            <div class="panel-header">
              <h2>{_escape_html(t("dashboard.log_title"))}</h2>
              <p>{_escape_html(t("dashboard.log_subtitle"))}</p>
            </div>
            <div class="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>{_escape_html(t("dashboard.table.time"))}</th>
                    <th>{_escape_html(t("dashboard.table.item"))}</th>
                    <th>{_escape_html(t("dashboard.table.quantity"))}</th>
                    <th>{_escape_html(t("dashboard.table.unit"))}</th>
                    <th>{_escape_html(t("dashboard.table.bring"))}</th>
                    <th>{_escape_html(t("dashboard.table.mealie"))}</th>
                  </tr>
                </thead>
                <tbody>
                  {''.join(rows) if rows else f'<tr><td colspan="6">{_escape_html(t("dashboard.table.empty"))}</td></tr>'}
                </tbody>
              </table>
            </div>
          </section>
        </main>
        <footer class="page-footer">
          <small>
            {_escape_html(t("dashboard.footer.project_by"))} <a href="mailto:soenke@soenkejacobs.de">Sönke Jacobs</a>
            · <a href="https://github.com/doenke/mealie2bring">{_escape_html(t("dashboard.footer.github"))}</a>
          </small>
        </footer>
      </body>
      <script>
        const translations = {translations_json};
        const triggerButton = document.getElementById("manual-trigger");
        const notice = document.getElementById("trigger-notice");

        const showNotice = (message, status) => {{
          notice.textContent = message;
          notice.classList.remove("is-success", "is-error");
          if (status) {{
            notice.classList.add(status);
          }}
        }};

        triggerButton.addEventListener("click", async () => {{
          triggerButton.disabled = true;
          showNotice(translations.noticeStarting);
          try {{
            const response = await fetch("/trigger", {{"method": "POST"}});
            if (!response.ok) {{
              throw new Error("request failed");
            }}
            await response.json();
            showNotice(translations.noticeStarted, "is-success");
          }} catch (error) {{
            showNotice(translations.noticeFailed, "is-error");
          }} finally {{
            triggerButton.disabled = false;
          }}
        }});
      </script>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/trigger")
async def manual_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_mealie_to_bring, "manual")
    return {"status": "triggered"}


@app.post("/api/trigger")
async def api_trigger(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_mealie_to_bring, "api")
    return {"status": "triggered"}


@app.post("/api/sync")
async def api_sync_now():
    results = await sync_mealie_to_bring("api")
    return {"status": "completed", "results": results}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    try:
        scheduler = app.state.scheduler
    except AttributeError:
        scheduler = None
    if scheduler is None:
        return

    if not scheduler.running:
        scheduler.start()

    for job in scheduler.get_jobs():
        if job.id == "mealie-bring-sync":
            job.remove()

    if settings.sync_interval_minutes > 0:
        scheduler.add_job(
            sync_mealie_to_bring,
            "interval",
            minutes=settings.sync_interval_minutes,
            id="mealie-bring-sync",
            max_instances=1,
            coalesce=True,
            kwargs={"trigger": "scheduler"},
        )


@app.on_event("shutdown")
async def shutdown_event():
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
