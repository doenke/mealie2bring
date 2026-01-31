# mealie2bring

Syncs open items from a Mealie shopping list to Bring! and checks them off in Mealie. The web UI shows the log and provides a manual trigger.
- Mealie is an Open-Source-Recepie-Manager, that can create shopping lists from recepies: https://github.com/mealie-recipes/mealie
- Bring! is a shopping list app with good family sharing capabilities and a smooth UI: https://www.getbring.com/

It preserves the quantities and units properly during the transfer to Bring.

## Features

- Fully configurable via environment variables
- Retains units and quantities
- Automatic sync on a configurable interval (default: 3 minutes)
- Log output in the console and in the web UI (max. 30 days)
- Manual trigger via button and via web service


## Quickstart (Docker Compose)

This compose is just a quickie... Find a full example in the repo:  [`compose.yaml`](./compose.yaml)

```yaml
services:
  mealie2bring:
    build: https://github.com/doenke/mealie2bring.git#main
    container_name: mealie2bring
    command: >
      uvicorn app.main:app
      --host 0.0.0.0 --port ${PORT:-1235}
      --proxy-headers --forwarded-allow-ips="*"
    ports:
      - "${PORT:-1235}:${PORT:-1235}"
    environment:
      MEALIE_BASE_URL: "https://mealie.example.com"
      MEALIE_API_TOKEN: "your-mealie-token"
      MEALIE_SHOPPING_LIST_ID: "your-shopping-list-id"
      BRING_EMAIL: "you@example.com"
      BRING_PASSWORD: "your-bring-password"
    restart: unless-stopped

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
| `SYNC_INTERVAL_MINUTES` | Sync interval in minutes (set to `0` to disable automatic sync) | `3` |
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
