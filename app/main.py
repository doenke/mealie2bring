from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
import asyncio
import uvicorn
from .sync import sync_mealie_to_bring
from pathlib import Path

app = FastAPI(title="Mealie → Bring Sync")

# Static files (optional)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.post("/trigger")
async def manual_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_mealie_to_bring)
    return {"status": "triggered"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
