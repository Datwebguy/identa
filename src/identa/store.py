"""SQLite intent store. The intent is written before any external call."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS intents (
    key TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    action TEXT NOT NULL,
    args_json TEXT NOT NULL,
    memory_json TEXT NOT NULL,
    branch TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS steps (
    key TEXT NOT NULL REFERENCES intents(key),
    step TEXT NOT NULL,
    state TEXT NOT NULL,
    at TEXT NOT NULL,
    PRIMARY KEY (key, step, state)
);
CREATE TABLE IF NOT EXISTS outcomes (
    key TEXT PRIMARY KEY REFERENCES intents(key),
    pr_url TEXT NOT NULL,
    memory_json TEXT NOT NULL,
    at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS human_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT,
    domain TEXT,
    reason TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    at TEXT NOT NULL
);
"""

PENDING = "pending"
COMPLETED = "completed"
NEEDS_HUMAN = "needs_human"
FINAL_STATES = (COMPLETED, "rejected", NEEDS_HUMAN)


def now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class Intent:
    key: str
    company_id: str
    action: str
    args_json: str
    memory_json: str
    branch: str
    state: str


class Store:
    def __init__(self, path: str | Path) -> None:
        self._db = sqlite3.connect(str(path), isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        self._db.close()

    def write_intent(
        self,
        key: str,
        company_id: str,
        action: str,
        args_json: str,
        memory_json: str,
        branch: str,
    ) -> bool:
        """Insert the intent as pending. Returns False if the key already exists."""
        cur = self._db.execute(
            "INSERT OR IGNORE INTO intents VALUES (?,?,?,?,?,?,?,?)",
            (key, company_id, action, args_json, memory_json, branch, PENDING, now()),
        )
        return cur.rowcount == 1

    def get_intent(self, key: str) -> Intent | None:
        row = self._db.execute("SELECT * FROM intents WHERE key=?", (key,)).fetchone()
        return self._intent(row) if row else None

    def find_by_company(self, company_id: str, action: str) -> Intent | None:
        row = self._db.execute(
            "SELECT * FROM intents WHERE company_id=? AND action=? ORDER BY created_at LIMIT 1",
            (company_id, action),
        ).fetchone()
        return self._intent(row) if row else None

    def set_state(self, key: str, state: str) -> None:
        self._db.execute("UPDATE intents SET state=? WHERE key=?", (state, key))

    def unfinished(self) -> list[Intent]:
        marks = ",".join("?" for _ in FINAL_STATES)
        rows = self._db.execute(
            f"SELECT * FROM intents WHERE state NOT IN ({marks}) ORDER BY created_at",
            FINAL_STATES,
        ).fetchall()
        return [self._intent(r) for r in rows]

    def log_step(self, key: str, step: str, state: str) -> None:
        self._db.execute("INSERT OR IGNORE INTO steps VALUES (?,?,?,?)", (key, step, state, now()))

    def steps(self, key: str) -> list[tuple[str, str]]:
        rows = self._db.execute(
            "SELECT step, state FROM steps WHERE key=? ORDER BY at, rowid", (key,)
        ).fetchall()
        return [(r["step"], r["state"]) for r in rows]

    def commit_outcome(self, key: str, pr_url: str, memory_json: str) -> None:
        """Outcome, memory row and intent state change in one transaction."""
        self._db.execute("BEGIN")
        try:
            self._db.execute(
                "INSERT OR REPLACE INTO outcomes VALUES (?,?,?,?)",
                (key, pr_url, memory_json, now()),
            )
            self._db.execute("UPDATE intents SET state=? WHERE key=?", (COMPLETED, key))
            self._db.execute("COMMIT")
        except BaseException:
            self._db.execute("ROLLBACK")
            raise

    def outcome_pr_url(self, key: str) -> str | None:
        row = self._db.execute("SELECT pr_url FROM outcomes WHERE key=?", (key,)).fetchone()
        return str(row["pr_url"]) if row else None

    def enqueue_human(
        self, key: str | None, domain: str | None, reason: str, detail_json: str
    ) -> None:
        """Queue once: an identical pending entry is not added again on a re-run."""
        dup = self._db.execute(
            "SELECT 1 FROM human_queue WHERE status='pending' AND key IS ? AND domain IS ? "
            "AND reason=?",
            (key, domain, reason),
        ).fetchone()
        if dup:
            return
        self._db.execute(
            "INSERT INTO human_queue (key, domain, reason, detail_json, at) VALUES (?,?,?,?,?)",
            (key, domain, reason, detail_json, now()),
        )

    def human_queue(self) -> list[sqlite3.Row]:
        return self._db.execute("SELECT * FROM human_queue WHERE status='pending'").fetchall()

    def get_queue_item(self, item_id: int) -> sqlite3.Row | None:
        row: sqlite3.Row | None = self._db.execute(
            "SELECT * FROM human_queue WHERE id=?", (item_id,)
        ).fetchone()
        return row

    def resolve_queue_item(self, item_id: int, status: str) -> None:
        self._db.execute("UPDATE human_queue SET status=? WHERE id=?", (status, item_id))

    @staticmethod
    def _intent(row: sqlite3.Row) -> Intent:
        return Intent(
            row["key"],
            row["company_id"],
            row["action"],
            row["args_json"],
            row["memory_json"],
            row["branch"],
            row["state"],
        )
