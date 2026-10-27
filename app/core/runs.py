"""SQLite run policy for a local trusted launcher.

Inputs are validated by the biological gate before ``create``. Approval, ownership,
budget changes and dispatch claims are trusted-host operations, never model tools.
Every adapter must reserve and atomically claim before making an external call.
There is deliberately no automatic retry or reset of an uncertain dispatch.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator, Mapping
import uuid

from app.core.budget import Approval, BudgetError, OwnershipError, PolicyError, Reservation, nonnegative_int


def _text(value: str, name: str, maximum: int = 200) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise PolicyError(f"Invalid {name}")
    return value


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


class RunService:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        # The path is a launcher configuration, not model-controlled input.
        if self.db_path == ":memory:":
            raise PolicyError("A durable SQLite file is required")
        with self._transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY, owner TEXT NOT NULL, input_json TEXT NOT NULL,
                plan_digest TEXT NOT NULL, budget_version INTEGER NOT NULL,
                usd_micros INTEGER NOT NULL, max_meta_requests INTEGER NOT NULL,
                approved_digest TEXT, approved_version INTEGER,
                state TEXT NOT NULL, cancellation_requested INTEGER NOT NULL DEFAULT 0)""")
            db.execute("""CREATE TABLE IF NOT EXISTS reservations (
                task_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
                job_digest TEXT NOT NULL, estimate_micros INTEGER NOT NULL,
                kind TEXT NOT NULL, status TEXT NOT NULL, provider_job_id TEXT,
                actual_micros INTEGER, UNIQUE(run_id,job_digest))""")
            db.execute("""CREATE TABLE IF NOT EXISTS run_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(run_id),
                event_kind TEXT NOT NULL, details_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))""")
        with self._connection() as db:
            db.execute("PRAGMA journal_mode=WAL")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
            except BaseException:
                db.rollback()
                raise
            else:
                db.commit()

    def _owned(self, db: sqlite3.Connection, run_id: str, owner_id: str) -> sqlite3.Row:
        _text(owner_id, "owner")
        row = db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or row["owner"] != owner_id:
            raise OwnershipError("Run unavailable to this owner")
        return row

    @staticmethod
    def _task(db: sqlite3.Connection, run_id: str, task_id: str) -> sqlite3.Row:
        row = db.execute("SELECT * FROM reservations WHERE run_id=? AND task_id=?", (run_id, task_id)).fetchone()
        if row is None:
            raise PolicyError("Task does not belong to this run")
        return row

    @staticmethod
    def _event(db: sqlite3.Connection, run_id: str, kind: str, **details: Any) -> None:
        db.execute("INSERT INTO run_events(run_id,event_kind,details_json) VALUES (?,?,?)",
                   (run_id, kind, _json(details)))

    @staticmethod
    def _committed(db: sqlite3.Connection, run_id: str) -> int:
        return db.execute("SELECT COALESCE(SUM(COALESCE(actual_micros,estimate_micros)),0) FROM reservations WHERE run_id=?",
                          (run_id,)).fetchone()[0]

    @staticmethod
    def _meta_count(db: sqlite3.Connection, run_id: str) -> int:
        return db.execute("SELECT COUNT(*) FROM reservations WHERE run_id=? AND kind='meta'", (run_id,)).fetchone()[0]

    def _conflict(self, db: sqlite3.Connection, run: sqlite3.Row) -> bool:
        return (self._committed(db, run["run_id"]) > run["usd_micros"]
                or self._meta_count(db, run["run_id"]) > run["max_meta_requests"])

    def _authorized(self, db: sqlite3.Connection, run: sqlite3.Row) -> None:
        if run["state"] == "CANCELLED":
            raise PolicyError("Run is cancelled")
        if run["approved_digest"] != run["plan_digest"] or run["approved_version"] != run["budget_version"]:
            raise PolicyError("Current plan and budget require explicit approval")
        if self._conflict(db, run):
            raise BudgetError("Committed usage exceeds the current budget or request ceiling")

    def create(self, validated_input: Mapping[str, Any], owner_id: str) -> str:
        _text(owner_id, "owner")
        if not isinstance(validated_input, Mapping):
            raise PolicyError("Expected validated input mapping")
        budget = validated_input.get("requested_budget", {})
        if not isinstance(budget, Mapping):
            raise PolicyError("Expected requested_budget mapping")
        limit = nonnegative_int(budget.get("usd_micros", 0), "usd_micros")
        requests = nonnegative_int(budget.get("max_meta_requests", 0), "max_meta_requests")
        if requests > 12:
            raise PolicyError("At most 12 Meta requests are supported per run")
        body = _json(validated_input)
        run_id = uuid.uuid4().hex
        digest = hashlib.sha256(body.encode("ascii")).hexdigest()
        with self._transaction() as db:
            db.execute("""INSERT INTO runs(run_id,owner,input_json,plan_digest,budget_version,usd_micros,
                       max_meta_requests,state) VALUES (?,?,?,?,1,?,?,?)""",
                       (run_id, owner_id, body, digest, limit, requests, "AWAITING_APPROVAL"))
            self._event(db, run_id, "created", plan_digest=digest, budget_version=1)
        return run_id

    def get(self, run_id: str, owner_id: str) -> dict:
        with self._transaction() as db:
            row = self._owned(db, run_id, owner_id)
            tasks = [dict(r) for r in db.execute("SELECT * FROM reservations WHERE run_id=? ORDER BY rowid", (run_id,))]
            committed = self._committed(db, run_id)
            known = sum(t["actual_micros"] for t in tasks if t["actual_micros"] is not None)
            all_known = bool(tasks) and all(t["actual_micros"] is not None for t in tasks)
            return {"run_id": run_id, "input": json.loads(row["input_json"]),
                    "plan_digest": row["plan_digest"], "budget_version": row["budget_version"],
                    "state": row["state"], "usd_micros": row["usd_micros"],
                    "max_meta_requests": row["max_meta_requests"],
                    "meta_requests_reserved": sum(t["kind"] == "meta" for t in tasks),
                    "committed_micros": committed, "actual_cost_micros": known if all_known else None,
                    "known_actual_cost_micros": known, "cost_status": "actual" if all_known else "unknown",
                    "budget_conflict": self._conflict(db, row),
                    "cancellation_requested": bool(row["cancellation_requested"]), "tasks": tasks}

    def approve(self, run_id: str, plan_digest: str, budget_version: int, owner_id: str) -> Approval:
        with self._transaction() as db:
            row = self._owned(db, run_id, owner_id)
            if row["state"] == "CANCELLED":
                raise PolicyError("Run is cancelled")
            if plan_digest != row["plan_digest"] or type(budget_version) is not int or budget_version != row["budget_version"]:
                raise PolicyError("Approval does not match the frozen plan and budget version")
            if self._conflict(db, row):
                raise BudgetError("Cannot approve limits below committed usage")
            db.execute("UPDATE runs SET approved_digest=?,approved_version=?,state='QUEUED',cancellation_requested=0 WHERE run_id=?",
                       (plan_digest, budget_version, run_id))
            self._event(db, run_id, "approved", plan_digest=plan_digest, budget_version=budget_version)
        return Approval(run_id, plan_digest, budget_version)

    def reserve(self, run_id: str, job_digest: str, estimate_micros: int, owner_id: str, *, kind: str = "science") -> Reservation:
        _text(job_digest, "job digest", 128)
        nonnegative_int(estimate_micros, "estimate_micros")
        if kind not in {"science", "meta"}:
            raise PolicyError("Unsupported reservation kind")
        with self._transaction() as db:
            run = self._owned(db, run_id, owner_id)
            existing = db.execute("SELECT * FROM reservations WHERE run_id=? AND job_digest=?", (run_id, job_digest)).fetchone()
            if existing is not None:
                if existing["estimate_micros"] != estimate_micros or existing["kind"] != kind:
                    raise PolicyError("Idempotency key reused with different job parameters")
                return self._reservation(existing, False)
            self._authorized(db, run)
            if self._committed(db, run_id) + estimate_micros > run["usd_micros"]:
                raise BudgetError("Reservation would exceed the approved budget")
            if kind == "meta":
                count = self._meta_count(db, run_id)
                if count >= run["max_meta_requests"]:
                    raise BudgetError("Meta request ceiling reached")
            task_id = uuid.uuid4().hex
            db.execute("""INSERT INTO reservations(task_id,run_id,job_digest,estimate_micros,kind,status)
                       VALUES (?,?,?,?,?,'RESERVED')""", (task_id, run_id, job_digest, estimate_micros, kind))
            self._event(db, run_id, "reserved", task_id=task_id, estimate_micros=estimate_micros, job_kind=kind)
            return self._reservation(self._task(db, run_id, task_id), True)

    @staticmethod
    def _reservation(row: sqlite3.Row, is_new: bool) -> Reservation:
        return Reservation(row["task_id"], row["run_id"], row["job_digest"], row["estimate_micros"],
                           row["status"], row["provider_job_id"], is_new)

    def claim(self, run_id: str, task_id: str, owner_id: str) -> bool:
        """Atomically authorize exactly one dispatch. False means do not call a provider."""
        with self._transaction() as db:
            run = self._owned(db, run_id, owner_id)
            task = self._task(db, run_id, task_id)
            if task["status"] != "RESERVED" or run["state"] == "CANCELLED":
                return False
            self._authorized(db, run)
            if db.execute("SELECT 1 FROM reservations WHERE run_id=? AND status IN ('DISPATCHED','UNKNOWN') LIMIT 1", (run_id,)).fetchone():
                return False
            db.execute("UPDATE reservations SET status='DISPATCHED' WHERE task_id=?", (task_id,))
            db.execute("UPDATE runs SET state='RUNNING' WHERE run_id=?", (run_id,))
            self._event(db, run_id, "dispatched", task_id=task_id)
            return True

    def attach_provider_job(self, run_id: str, task_id: str, owner_id: str, provider_job_id: str) -> None:
        _text(provider_job_id, "provider job ID", 300)
        with self._transaction() as db:
            self._owned(db, run_id, owner_id)
            task = self._task(db, run_id, task_id)
            if task["status"] not in {"DISPATCHED", "UNKNOWN"}:
                raise PolicyError("Only a dispatched task can have a provider job")
            if task["provider_job_id"] not in {None, provider_job_id}:
                raise PolicyError("Provider job identity is immutable")
            db.execute("UPDATE reservations SET provider_job_id=? WHERE task_id=?", (provider_job_id, task_id))
            self._event(db, run_id, "provider_job_recorded", task_id=task_id, provider_job_id=provider_job_id)

    def mark_unknown(self, run_id: str, task_id: str, owner_id: str) -> None:
        with self._transaction() as db:
            self._owned(db, run_id, owner_id)
            task = self._task(db, run_id, task_id)
            if task["status"] not in {"DISPATCHED", "UNKNOWN"}:
                raise PolicyError("Only a dispatched task can have an unknown outcome")
            db.execute("UPDATE reservations SET status='UNKNOWN' WHERE task_id=?", (task_id,))
            self._event(db, run_id, "outcome_unknown", task_id=task_id)

    def settle(self, run_id: str, task_id: str, owner_id: str, *, actual_micros: int | None = None) -> None:
        """Record completion; unknown price retains the conservative reservation."""
        if actual_micros is not None:
            nonnegative_int(actual_micros, "actual_micros")
        with self._transaction() as db:
            run = self._owned(db, run_id, owner_id)
            task = self._task(db, run_id, task_id)
            if task["status"] == "SETTLED":
                if task["actual_micros"] != actual_micros:
                    raise PolicyError("Settled actual cost cannot be overwritten")
                return
            if task["status"] not in {"DISPATCHED", "UNKNOWN", "COMPLETED_UNKNOWN_COST"}:
                raise PolicyError("A reservation cannot settle before dispatch")
            status = "SETTLED" if actual_micros is not None else "COMPLETED_UNKNOWN_COST"
            db.execute("UPDATE reservations SET status=?,actual_micros=? WHERE task_id=?", (status, actual_micros, task_id))
            conflict = self._conflict(db, run)
            if conflict and run["state"] != "CANCELLED":
                db.execute("UPDATE runs SET state='BLOCKED',cancellation_requested=1 WHERE run_id=?", (run_id,))
            self._event(db, run_id, "settled", task_id=task_id, actual_micros=actual_micros, budget_conflict=conflict)

    def set_budget(self, run_id: str, owner_id: str, usd_micros: int, *, max_meta_requests: int | None = None) -> int:
        """Invalidate approval. Already incurred/reserved usage is never erased."""
        nonnegative_int(usd_micros, "usd_micros")
        if max_meta_requests is not None:
            nonnegative_int(max_meta_requests, "max_meta_requests")
            if max_meta_requests > 12:
                raise PolicyError("At most 12 Meta requests are supported per run")
        with self._transaction() as db:
            run = self._owned(db, run_id, owner_id)
            if run["state"] == "CANCELLED":
                raise PolicyError("Run is cancelled")
            requests = run["max_meta_requests"] if max_meta_requests is None else max_meta_requests
            version = run["budget_version"] + 1
            conflict = (self._committed(db, run_id) > usd_micros
                        or self._meta_count(db, run_id) > requests)
            lower = usd_micros < run["usd_micros"] or requests < run["max_meta_requests"]
            state = "BLOCKED" if conflict else "AWAITING_APPROVAL"
            db.execute("""UPDATE runs SET usd_micros=?,max_meta_requests=?,budget_version=?,
                       approved_digest=NULL,approved_version=NULL,state=?,cancellation_requested=? WHERE run_id=?""",
                       (usd_micros, requests, version, state, int(lower), run_id))
            self._event(db, run_id, "budget_changed", budget_version=version, usd_micros=usd_micros,
                        max_meta_requests=requests, budget_conflict=conflict)
            return version

    def cancel(self, run_id: str, owner_id: str) -> None:
        with self._transaction() as db:
            self._owned(db, run_id, owner_id)
            db.execute("UPDATE runs SET state='CANCELLED',cancellation_requested=1 WHERE run_id=?", (run_id,))
            self._event(db, run_id, "cancelled")

    def events(self, run_id: str, owner_id: str) -> list[dict]:
        with self._transaction() as db:
            self._owned(db, run_id, owner_id)
            return [{"event_id": row["event_id"], "kind": row["event_kind"],
                     "details": json.loads(row["details_json"]), "created_at": row["created_at"]}
                    for row in db.execute("SELECT * FROM run_events WHERE run_id=? ORDER BY event_id", (run_id,))]
