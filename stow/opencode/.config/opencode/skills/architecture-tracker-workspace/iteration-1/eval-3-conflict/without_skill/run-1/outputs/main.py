from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DB_FILE = Path("sequences.db")

app = FastAPI(title="Graph Viewer")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db() -> None:
    conn = _get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sequences (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            data TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _migrate_from_json() -> None:
    json_path = Path("sequences.json")
    if not json_path.exists():
        return
    existing = json.loads(json_path.read_text(encoding="utf-8"))
    if not existing:
        return
    conn = _get_conn()
    for s in existing:
        conn.execute(
            "INSERT OR IGNORE INTO sequences (id, name, data, updated_at) VALUES (?, ?, ?, ?)",
            (s["id"], s["name"], json.dumps(s["data"]), s["updated_at"]),
        )
    conn.commit()
    conn.close()
    json_path.rename(json_path.with_suffix(".json.bak"))


_init_db()
_migrate_from_json()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SequenceCreate(BaseModel):
    name: str
    data: list[float]


class SequenceOut(BaseModel):
    id: str
    name: str
    data: list[float]
    updated_at: str


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def _row_to_out(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "data": json.loads(row["data"]),
        "updated_at": row["updated_at"],
    }


@app.get("/api/sequences", response_model=list[SequenceOut])
def list_sequences():
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM sequences ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [_row_to_out(r) for r in rows]


@app.post("/api/sequences", response_model=SequenceOut, status_code=201)
def create_sequence(body: SequenceCreate):
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    seq_id = uuid.uuid4().hex[:12]
    conn.execute(
        "INSERT INTO sequences (id, name, data, updated_at) VALUES (?, ?, ?, ?)",
        (seq_id, body.name.strip(), json.dumps(body.data), now),
    )
    conn.commit()
    conn.close()
    return {"id": seq_id, "name": body.name.strip(), "data": body.data, "updated_at": now}


@app.put("/api/sequences/{seq_id}", response_model=SequenceOut)
def update_sequence(seq_id: str, body: SequenceCreate):
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "UPDATE sequences SET name = ?, data = ?, updated_at = ? WHERE id = ?",
        (body.name.strip(), json.dumps(body.data), now, seq_id),
    )
    conn.commit()
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "sequence not found")
    conn.close()
    return {"id": seq_id, "name": body.name.strip(), "data": body.data, "updated_at": now}


@app.delete("/api/sequences/{seq_id}", status_code=204)
def delete_sequence(seq_id: str):
    conn = _get_conn()
    cur = conn.execute("DELETE FROM sequences WHERE id = ?", (seq_id,))
    conn.commit()
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "sequence not found")
    conn.close()


# ---------------------------------------------------------------------------
# Static files (must be last)
# ---------------------------------------------------------------------------

static = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static), html=True), name="static")
