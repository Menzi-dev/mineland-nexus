import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4
from .geometry import DATA_DIR


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection():
    db = sqlite3.connect(DATA_DIR / "assessments.sqlite", timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, created TEXT NOT NULL, body TEXT NOT NULL)")
    try:
        with db:
            yield db
    finally:
        db.close()


def save(kind, body, record_id=None):
    record_id = record_id or uuid4().hex
    body = {**body, "id": record_id}
    with connection() as db:
        db.execute("INSERT INTO records VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                   (record_id, kind, body.get("created_at", now()), json.dumps(body, allow_nan=False)))
    return body


def get(record_id, kind):
    with connection() as db:
        row = db.execute("SELECT body FROM records WHERE id=? AND kind=?", (record_id, kind)).fetchone()
    return json.loads(row[0]) if row else None


def listing(kind):
    with connection() as db:
        rows = db.execute("SELECT body FROM records WHERE kind=? ORDER BY created DESC LIMIT 100", (kind,)).fetchall()
    return [json.loads(row[0]) for row in rows]


def recover_interrupted():
    for record in listing("assessment"):
        if record["status"] in ("queued", "running"):
            save("assessment", {**record, "status": "interrupted", "stage": "Server restarted. Run this assessment again."}, record["id"])
