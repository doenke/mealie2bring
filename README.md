# mealie2bring

Syncs open items from a Mealie shopping list to Bring! and checks them off in Mealie. The web UI shows the log and provides a manual trigger.
Mealie ist ein Open-Source-Rezept- und Küchenmanager, der Einkaufslisten aus Rezepten erzeugt und verwaltet: https://github.com/mealie-recipes/mealie
Bring! ist eine Einkaufslisten-App, mit der sich geteilte Listen verwalten und abhaken lassen: https://www.getbring.com/

## Features

- Fully configurable via environment variables
- Automatic sync on a configurable interval (default: 3 minutes)
- Log output in the console and in the web UI (max. 30 days)
- Manual trigger via button and via web service
- Docker & Docker Compose setup on port 1235 (configurable via `PORT`)

## Quickstart (Docker Compose)

```bash
docker compose up -d --build
```

The UI is then available at `http://localhost:1235` (or `http://localhost:$PORT` if you override the port).

## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `MEALIE_BASE_URL` | Base URL of the Mealie instance | `http://localhost:9000` |
| `MEALIE_API_TOKEN` | API token for Mealie | empty |
| `MEALIE_SHOPPING_LIST_ID` | Shopping list ID in Mealie | empty |
| `BRING_EMAIL` | Bring login email | empty |
| `BRING_PASSWORD` | Bring password | empty |
| `BRING_LIST_UUID` | Optional: Bring list UUID (overrides login response) | empty |
| `SYNC_INTERVAL_MINUTES` | Sync interval in minutes | `3` |
| `LOG_RETENTION_DAYS` | Log retention in days | `30` |
| `LOG_PATH` | Path to the log file | `/data/mealie_bring_sync.log` |
| `PORT` | Web server port | `1235` |
| `DASHBOARD_LOGO_URL` | Optional: URL for a logo shown in the dashboard header | empty |

## Endpoints

- `GET /` – Dashboard with log table
- `POST /trigger` – Manual sync (button)
- `POST /api/trigger` – Manual sync via web service (async)
- `POST /api/sync` – Manual sync via web service (sync, returns results)
- `GET /health` – Health check

## Notes

- The log can persist across restarts when `/data` is mounted.
- Only the last 30 days of entries are kept.
