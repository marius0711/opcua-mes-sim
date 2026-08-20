# opcua-mes-sim

A lite, self-contained OPC UA measurement pipeline: a simulated robot arm exposes sensor
data over OPC UA, a client polls and evaluates it (FFT-based vibration analysis), results
are persisted in SQLite and served through a REST API — with a small CI pipeline and a
Docker Compose setup tying the pieces together.

The scope is intentionally reduced compared to a production MES stack, to keep the project
focused on the OPC UA integration itself rather than on infrastructure incidental to it.

## Scope

- **OPC UA only** — no MQTT or other messaging layers.
- **SQLite** instead of Postgres — a single file, no separate database service to operate.
- **Docker Compose** — three services (server, client, API) communicating over a container
  network, backed by a shared volume for the SQLite file.

## Architecture

```
opcua_server/   simulated OPC UA server (asyncua) — robot arm with 5 nodes
opcua_client/   polls the server, computes metrics, persists runs to SQLite
db/             SQLite schema + storage layer
report/         aggregates runs into a readable report, flags outlier runs
api/            FastAPI endpoint serving the latest evaluation results
tests/          pytest suite (transform, storage, report, API)
```

## Data flow

1. `opcua_server/server.py` simulates a robot arm axis: position, vibration, torque, cycle
   count, and a writable `TargetFrequencyHz` config node used to vary the simulated signal
   between runs.
2. `opcua_client/client.py` (or `multi_run.py` for several runs in sequence) polls the nodes,
   runs an FFT to find the vibration peak, computes position repeatability and torque
   outliers, and writes everything to `measurement_run` / `measurement_point` /
   `evaluation_result` in SQLite.
3. `report/report.py` aggregates runs and flags any whose vibration peak deviates from the
   group median beyond a threshold.
4. `api/main.py` exposes the latest evaluation results as JSON at `/results` — it reads only
   from SQLite and has no dependency on a live OPC UA connection.

## Running locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 -m opcua_server.server        # terminal 1
python3 -m opcua_client.multi_run     # terminal 2
uvicorn api.main:app --reload         # terminal 3
```

## Running with Docker Compose

```bash
docker compose up -d opcua-server api
docker compose run --rm client
curl http://localhost:8000/results
```

## Tests / CI

```bash
pytest tests/ -v
```

Runs automatically on every push via GitHub Actions (`.github/workflows/ci.yml`).
