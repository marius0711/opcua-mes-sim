# opcua-mes-sim

A lite, self-contained OPC UA measurement pipeline. A simulated robot arm exposes sensor
data over OPC UA, a client polls and evaluates it (FFT-based vibration analysis), results
are persisted in SQLite and served through a REST API, with a small CI pipeline and a
Docker Compose setup tying the pieces together.

The scope is intentionally reduced compared to a production MES stack, to keep the project
focused on the OPC UA integration itself rather than on infrastructure incidental to it.

## Scope

The MVP is scoped around a single protocol and a minimal, easy to operate stack, so the
OPC UA integration stays the center of attention rather than competing with unrelated setup
work.

* **OPC UA** carries the entire data path from sensor node to client, keeping the project
  centered on one well established industrial protocol end to end.
* **SQLite** provides persistence as a single file, which keeps the project approachable:
  anyone can clone the repo and run it without standing up a separate database service.
* **Docker Compose** packages the three services (server, client, API) so they can be
  started, networked, and torn down as one reproducible unit.

## Architecture

```
opcua_server/   simulated OPC UA server (asyncua), robot arm with 5 nodes
opcua_client/   polls the server, computes metrics, persists runs to SQLite
db/             SQLite schema and storage layer
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
4. `api/main.py` exposes the latest evaluation results as JSON at `/results`. It reads only
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
python -m pytest tests/ -v
```

Runs automatically on every push via GitHub Actions (`.github/workflows/ci.yml`).

## Results

* All planned components (server, client, signal transform, storage, report, API, CI) are
  implemented and verified end to end, both locally and via Docker Compose.
* 11 automated tests cover the transform, storage, report, and API layers in isolation,
  independent of a running OPC UA server.
* The CI pipeline runs the full test suite on every push and is currently green.

## Value

The project demonstrates a working, reproducible OPC UA integration in miniature: a
simulated industrial data source, a client that turns raw signals into meaningful metrics,
traceable persistence keyed by run, an aggregation step that flags outliers, and a REST
interface a consuming system could use the way an MES would. It closes a specific skill gap
around OPC UA in a compact reference implementation rather than a toy example, and every
component was verified against a real running system, not assumed to work from the code
alone.

## Known issues encountered and how they were handled

Three real issues surfaced during development and testing. Each was diagnosed to its root
cause, fixed, and re-verified.

1. **Signal processing.** The FFT initially used a fixed, assumed sample rate instead of the
   one actually achieved by network polling, which shifted the detected peak frequency by
   roughly 65%. Fixed by measuring the achieved rate from real timestamps instead of
   assuming it.
2. **Container orchestration.** `depends_on` in Docker Compose only ordered container start,
   not application readiness, causing a `ConnectionRefusedError` when the client started
   before the OPC UA server had finished binding its port. Fixed with a TCP healthcheck and
   `condition: service_healthy`.
3. **CI tooling.** The GitHub Actions workflow invoked `pytest` directly instead of
   `python -m pytest`, so the project root was missing from the Python path and imports
   failed on the runner despite passing locally. Fixed by aligning the CI command with the
   local one.

All three are now covered by the test suite and the CI pipeline, so a regression in any of
them would be caught automatically going forward.
