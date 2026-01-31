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

Die Oberfläche ist anschließend unter `http://localhost:1235` erreichbar.

## Konfiguration

| Variable | Beschreibung | Standard |
| --- | --- | --- |
| `MEALIE_BASE_URL` | Basis-URL der Mealie-Instanz | `http://localhost:9000` |
| `MEALIE_API_TOKEN` | API Token für Mealie | leer |
| `MEALIE_SHOPPING_LIST_ID` | Shopping-List-ID in Mealie | leer |
| `BRING_EMAIL` | Bring Login E-Mail | leer |
| `BRING_PASSWORD` | Bring Passwort | leer |
| `BRING_LIST_UUID` | Optional: Bring List UUID (überschreibt Login-Antwort) | leer |
| `SYNC_INTERVAL_MINUTES` | Intervall in Minuten | `3` |
| `LOG_RETENTION_DAYS` | Aufbewahrungsdauer Log | `30` |
| `LOG_PATH` | Pfad zur Log-Datei | `/data/mealie_bring_sync.log` |
| `PORT` | Port für den Webserver | `1235` |

## Endpoints

- `GET /` – Dashboard mit Log-Tabelle
- `POST /trigger` – manueller Sync (Button)
- `POST /api/trigger` – manueller Sync via Webservice (asynchron)
- `POST /api/sync` – manueller Sync via Webservice (synchron, gibt Ergebnisse zurück)
- `GET /health` – Healthcheck

## Hinweise

- Das Log bleibt bei Neustart optional erhalten, wenn `/data` gemountet wird.
- Es werden maximal die letzten 30 Tage Log-Einträge behalten.
