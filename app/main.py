import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .scheduler import create_scheduler
from .settings import get_settings
from .sync import load_log_entries, sync_mealie_to_bring

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="Mealie → Bring Sync")
app.state.scheduler = create_scheduler()

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def _format_timestamp(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    localized = parsed.astimezone()
    return localized.strftime("%d.%m.%Y %H:%M")


def _format_now() -> str:
    return _format_timestamp(datetime.now(timezone.utc).isoformat())


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    settings = get_settings()
    entries = load_log_entries(settings)
    last_sync_entry = next(
        (
            entry
            for entry in entries
            if entry.get("type") == "event" and entry.get("message") == "Sync gestartet"
        ),
        None,
    )
    last_sync_display = (
        _format_timestamp(last_sync_entry.get("timestamp", "")) if last_sync_entry else "Noch kein Lauf"
    )
    page_generated = _format_now()
    custom_logo_html = ""
    if settings.dashboard_logo_url:
        custom_logo_html = (
            f'<div class="logo logo--custom actions-logo"><img src="{settings.dashboard_logo_url}" alt="Logo" /></div>'
        )
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
        '<button type="button" id="manual-trigger">Manuell starten</button>'
        "</div>"
    )
    status_labels = {
        "ok": "übernommen",
    }
    mealie_labels = {
        "done": "erledigt",
    }
    rows = []
    for entry in entries:
        if entry.get("type") != "item":
            continue
        status_value = entry.get("status", "")
        status_label = status_labels.get(status_value, status_value)
        mealie_value = entry.get("mealie", "-")
        mealie_label = mealie_labels.get(mealie_value, mealie_value)
        mealie_class = f" class='{mealie_value}'" if mealie_value and mealie_value != "-" else ""
        rows.append(
            f"<tr>"
            f"<td>{_format_timestamp(entry.get('timestamp',''))}</td>"
            f"<td>{entry.get('name','')}</td>"
            f"<td>{entry.get('quantity') or ''}</td>"
            f"<td>{entry.get('unit') or ''}</td>"
            f"<td class='{status_value}'>{status_label}</td>"
            f"<td{mealie_class}>{mealie_label}</td>"
            f"</tr>"
        )

    sync_label = (
        "Automatischer Abruf deaktiviert"
        if settings.sync_interval_minutes <= 0
        else f"Abruf alle {settings.sync_interval_minutes} Minuten"
    )
    html = f"""
    <!DOCTYPE html>
    <html lang="de">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Mealie → Bring</title>
        <link rel="stylesheet" href="/static/style.css" />
        <link rel="icon" type="image/png" href="/static/Mealie2Bring.png" />
      </head>
      <body>
        <main class="container">
          <header class="header">
            <div class="header-title">
              {logo_html}
              <div>
              <p class="eyebrow">mealie2bring</p>
              <h1>Mealie → Bring</h1>
              <p class="subtitle">{sync_label}</p>
              <div class="status-meta">
                <p class="meta-line">Letzter Lauf: {last_sync_display}</p>
                <p class="meta-line">Seite erstellt: {page_generated}</p>
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
              <h2>Log</h2>
              <p>Letzte 30 Tage (max).</p>
            </div>
            <div class="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Zeit</th>
                    <th>Artikel</th>
                    <th>Menge</th>
                    <th>Einheit</th>
                    <th>Bring</th>
                    <th>Mealie</th>
                  </tr>
                </thead>
                <tbody>
                  {''.join(rows) if rows else '<tr><td colspan="6">Noch keine Einträge</td></tr>'}
                </tbody>
              </table>
            </div>
          </section>
        </main>
        <footer class="page-footer">
          <small>
            Ein Projekt von <a href="mailto:soenke@soenkejacobs.de">Sönke Jacobs</a>
            · <a href="https://github.com/doenke/mealie2bring">GitHub</a>
          </small>
        </footer>
      </body>
      <script>
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
          showNotice("Manueller Sync wird gestartet …");
          try {{
            const response = await fetch("/trigger", {{"method": "POST"}});
            if (!response.ok) {{
              throw new Error("request failed");
            }}
            await response.json();
            showNotice("Sync angestoßen. Ergebnisse folgen im Log.", "is-success");
          }} catch (error) {{
            showNotice("Sync konnte nicht gestartet werden. Bitte erneut versuchen.", "is-error");
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
