import sqlite3

from fastapi import FastAPI

from db import store as db_store
from db.store import init_db
from report.report import fetch_run_summaries, flag_anomalies

app = FastAPI(title="opcua-mes-sim API")


@app.get("/results")
def get_results():
    conn = sqlite3.connect(db_store.DEFAULT_DB_PATH)
    init_db(conn)
    summaries = fetch_run_summaries(conn)
    summaries = flag_anomalies(summaries)
    conn.close()
    return summaries
