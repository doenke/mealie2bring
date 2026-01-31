# mealie2bring

Synchronisiert offene Einträge aus einer Mealie-Einkaufsliste nach Bring! und hakt sie in Mealie ab. Die Weboberfläche zeigt das Log an und bietet einen manuellen Start.

## Features

- Vollständig konfigurierbar über Umgebungsvariablen
- Automatischer Sync im einstellbaren Rhythmus (Default: 3 Minuten)
- Log-Ausgabe in der Konsole und Anzeige im Web-UI (max. 30 Tage)
- Manuelles Starten per Button und per Webservice
- Docker- & Docker-Compose-Setup auf Port 1235

## Schnellstart (Docker Compose)

```bash
docker compose up -d --build
```

The UI is then available at `http://localhost:1235`.

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

## Endpoints

- `GET /` – Dashboard with log table
- `POST /trigger` – Manual sync (button)
- `POST /api/trigger` – Manual sync via web service (async)
- `POST /api/sync` – Manual sync via web service (sync, returns results)
- `GET /health` – Health check

## Notes

- The log can persist across restarts when `/data` is mounted.
- Only the last 30 days of entries are kept.
