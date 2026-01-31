import logging
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


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    settings = get_settings()
    entries = load_log_entries(settings)
    logo_html = ""
    if settings.dashboard_logo_url:
        logo_html = (
            f'<img src="{settings.dashboard_logo_url}" alt="Logo" class="logo" />'
        )
    rows = []
    for entry in entries:
        if entry.get("type") != "item":
            continue
        rows.append(
            f"<tr>"
            f"<td>{entry.get('timestamp','')}</td>"
            f"<td>{entry.get('name','')}</td>"
            f"<td>{entry.get('note','')}</td>"
            f"<td class='{entry.get('status','')}'>{entry.get('status','')}</td>"
            f"<td>{entry.get('mealie','-')}</td>"
            f"</tr>"
        )

    html = f"""
    <!DOCTYPE html>
    <html lang="de">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Mealie → Bring</title>
        <link rel="stylesheet" href="/static/style.css" />
      </head>
      <body>
        <main class="container">
          <header class="header">
            <div class="header-title">
              {logo_html}
              <div>
              <p class="eyebrow">mealie2bring</p>
              <h1>Mealie → Bring</h1>
              <p class="subtitle">Letzter Abruf alle {settings.sync_interval_minutes} Minuten</p>
              </div>
            </div>
            <form method="post" action="/trigger">
              <button type="submit">Manuell starten</button>
            </form>
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
                    <th>Notiz</th>
                    <th>Status</th>
                    <th>Mealie</th>
                  </tr>
                </thead>
                <tbody>
                  {''.join(rows) if rows else '<tr><td colspan="5">Noch keine Einträge</td></tr>'}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </body>
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
