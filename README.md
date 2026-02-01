![mealie2bring Logo](./app/static/Mealie2Bring.png)

# mealie2bring
Syncs open items from a Mealie shopping list to Bring! and checks them off in Mealie. The web UI shows the log and provides a manual trigger next to a periodic poll.
- Mealie is an Open-Source-Recepie-Manager, that can create shopping lists from recepies: https://github.com/mealie-recipes/mealie
- Bring! is a shopping list app with good family sharing capabilities and a smooth UI: https://www.getbring.com/

It preserves the quantities and units properly during the transfer to Bring.


## Quickstart (Docker Compose)
Just get started with this compose. It contains everything you need to get going...

```yaml
services:
  mealie2bring:
    build: https://github.com/doenke/mealie2bring.git#main
    container_name: mealie2bring
    ports:
      - "1235:1235"
    environment:
      MEALIE_BASE_URL: "https://mealie.example.com"
      MEALIE_API_TOKEN: "your-mealie-token"
      MEALIE_SHOPPING_LIST_ID: "your-shopping-list-id"
      BRING_EMAIL: "you@example.com"
      BRING_PASSWORD: "your-bring-password"
    restart: unless-stopped
```
Find a full example in the repo:  [`docker-compose.yml`](./docker-compose.yml)

The UI is then available at `http://localhost:1235`. By default it is configured to run behind any reverse proxy.

## Finding your Mealie token and shopping list ID

1. In Mealie, go to **Settings → API Tokens** and create a new token. Use that value for `MEALIE_API_TOKEN`.
2. Open the shopping list you want to sync in your browser. Copy the list ID from the URL and use it for `MEALIE_SHOPPING_LIST_ID` (looks like: 5b43c28e-6f86-4c1f-9ad2-3c02f9d63c30`).

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
| `PROXY_HEADERS` | Enable uvicorn proxy headers (set to `false` to disable) | `true` |
| `FORWARDED_ALLOW_IPS` | Allowed IPs for proxy headers (uvicorn forwarded allow list) | `*` |
| `DASHBOARD_LOGO_URL` | Optional: URL for a logo shown in the dashboard header | empty |
| `UI_LOCALE` | Optional: Force UI locale (e.g. `de`, `en`, `de-DE`) | empty |
| `DASHBOARD_LOCALE` | Default locale used when none matches | `de` |
| `FALLBACK_LOCALE` | Fallback locale for missing translations | `en` |
| `DATE_FORMAT_DE` | Datetime format string for German locale | `%d.%m.%Y %H:%M` |
| `DATE_FORMAT_EN` | Datetime format string for English locale | `%Y-%m-%d %H:%M` |

## Endpoints

- `GET /` – Dashboard with log table
- `POST /trigger` – Manual sync (button)
- `POST /api/trigger` – Manual sync via web service (async)
- `POST /api/sync` – Manual sync via web service (sync, returns results)
- `GET /health` – Health check

## Notes

- The log can persist across restarts when `/data` is mounted.
