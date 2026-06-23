"""Append-only, hash-chained audit store (spec §5.5).

Follows the dual sqlite/Postgres pattern used by `app.settings_store` so
tests can run against a real database engine without a live Postgres
container. `write_record` is the only normal write path and only ever
INSERTs. `simulate_tampering` is a deliberately separate, demo-only method
that mutates a stored row in place to prove the chain detects tampering; no
other code path may call it.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from app.audit.models import GENESIS_PREV_HASH
from app.config import get_settings
from app.schemas.action import Action, EnforcementMode
from app.schemas.audit import EvidenceRecord, RecordType
from app.schemas.context import Context
from app.schemas.decision import Decision
from app.schemas.evidence import Evidence

def _to_jsonable(value: Any) -> Any:
    """Recursively convert a value into plain JSON-safe types."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


def canonical_json(payload: dict[str, Any]) -> str:
    """Sorted-keys, no-whitespace JSON used identically at write and verify time."""

    return json.dumps(_to_jsonable(payload), sort_keys=True, separators=(",", ":"))


def _hash_payload(row_without_id_and_hash: dict[str, Any], prev_hash: str) -> str:
    digest_input = canonical_json(row_without_id_and_hash) + prev_hash
    return sha256(digest_input.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ChainVerificationResult:
    """Outcome of walking the chain and recomputing every row's hash."""

    intact: bool
    verified_count: int
    broken_record_id: int | None
    broken_reason: str | None = None


@dataclass(frozen=True)
class AuditStore:
    """Append-only audit store with SHA-256 hash chaining.

    Default construction connects to Postgres using `app.config`. Tests may
    pass a `sqlite:///` URL to exercise identical persistence semantics
    without Docker.
    """

    database_url: str | None = None

    def write_record(
        self,
        *,
        action: Action,
        context_used: Context,
        evidence: Evidence,
        decision: Decision,
        enforcement_mode: EnforcementMode | str,
        executed: bool,
        record_type: RecordType | str,
        references_hash: str | None = None,
        human_approver: str | None = None,
        approval_reason: str | None = None,
        correlation_id: UUID | None = None,
    ) -> EvidenceRecord:
        """INSERT a new append-only row chained to the current tail. Never updates."""

        self._ensure_table()

        action_payload = action.model_dump(mode="json")
        context_payload = context_used.model_dump(mode="json")
        evidence_payload = evidence.model_dump(mode="json")
        decision_payload = decision.model_dump(mode="json")
        resolved_correlation_id = correlation_id or action.correlation_id
        created_at = datetime.now(timezone.utc)

        prev_hash = self._tail_hash()

        row_for_hash: dict[str, Any] = {
            "correlation_id": resolved_correlation_id,
            "action": action_payload,
            "context_used": context_payload,
            "evidence": evidence_payload,
            "decision": decision_payload,
            "enforcement_mode": str(enforcement_mode),
            "executed": executed,
            "record_type": str(record_type),
            "references_hash": references_hash,
            "human_approver": human_approver,
            "approval_reason": approval_reason,
            "created_at": created_at,
            "prev_hash": prev_hash,
        }
        record_hash = _hash_payload(row_for_hash, prev_hash)

        new_id = self._insert_row(
            correlation_id=resolved_correlation_id,
            action_payload=action_payload,
            context_payload=context_payload,
            evidence_payload=evidence_payload,
            decision_payload=decision_payload,
            enforcement_mode=str(enforcement_mode),
            executed=executed,
            record_type=str(record_type),
            references_hash=references_hash,
            human_approver=human_approver,
            approval_reason=approval_reason,
            created_at=created_at,
            record_hash=record_hash,
            prev_hash=prev_hash,
        )

        return EvidenceRecord(
            id=new_id,
            correlation_id=resolved_correlation_id,
            action=action,
            context_used=context_used,
            evidence=evidence,
            decision=decision,
            enforcement_mode=enforcement_mode,
            executed=executed,
            record_type=record_type,
            references_hash=references_hash,
            human_approver=human_approver,
            approval_reason=approval_reason,
            created_at=created_at,
            record_hash=record_hash,
            prev_hash=prev_hash,
        )

    def read_records(self) -> list[EvidenceRecord]:
        """Return all stored rows in insertion order, parsed back into EvidenceRecord."""

        self._ensure_table()
        return [self._row_to_record(row) for row in self._fetch_all_rows()]

    def verify_chain(self) -> ChainVerificationResult:
        """Recompute each row's expected hash and linkage; report the first break, if any."""

        self._ensure_table()
        raw_rows = self._fetch_all_rows()
        expected_prev_hash = GENESIS_PREV_HASH

        for index, raw in enumerate(raw_rows):
            row_for_hash = {
                "correlation_id": raw["correlation_id"],
                "action": raw["action"],
                "context_used": raw["context_used"],
                "evidence": raw["evidence"],
                "decision": raw["decision"],
                "enforcement_mode": raw["enforcement_mode"],
                "executed": raw["executed"],
                "record_type": raw["record_type"],
                "references_hash": raw["references_hash"],
                "human_approver": raw["human_approver"],
                "approval_reason": raw["approval_reason"],
                "created_at": raw["created_at"],
                "prev_hash": raw["prev_hash"],
            }

            if raw["prev_hash"] != expected_prev_hash:
                return ChainVerificationResult(
                    intact=False,
                    verified_count=index,
                    broken_record_id=raw["id"],
                    broken_reason="prev_hash linkage mismatch",
                )

            recomputed_hash = _hash_payload(row_for_hash, raw["prev_hash"])
            if recomputed_hash != raw["record_hash"]:
                return ChainVerificationResult(
                    intact=False,
                    verified_count=index,
                    broken_record_id=raw["id"],
                    broken_reason="record_hash mismatch",
                )

            expected_prev_hash = raw["record_hash"]

        return ChainVerificationResult(intact=True, verified_count=len(raw_rows), broken_record_id=None)

    def simulate_tampering(self, record_id: int, *, executed: bool | None = None) -> None:
        """Demo-only: mutate a stored row in place to demonstrate chain breakage.

        Not part of the normal write path and must never be called outside the
        tampering demonstration; it deliberately bypasses hashing and directly
        UPDATEs the targeted row's `executed` flag without recomputing the chain.
        """

        new_executed = (not self._fetch_row(record_id)["executed"]) if executed is None else executed
        self._update_executed(record_id, new_executed)

    @property
    def _uses_sqlite(self) -> bool:
        return bool(self.database_url and self.database_url.startswith("sqlite:///"))

    def _tail_hash(self) -> str:
        rows = self._fetch_all_rows()
        if not rows:
            return GENESIS_PREV_HASH
        return rows[-1]["record_hash"]

    def _row_to_record(self, raw: dict[str, Any]) -> EvidenceRecord:
        return EvidenceRecord(
            id=raw["id"],
            correlation_id=raw["correlation_id"],
            action=Action.model_validate(raw["action"]),
            context_used=Context.model_validate(raw["context_used"]),
            evidence=Evidence.model_validate(raw["evidence"]),
            decision=Decision.model_validate(raw["decision"]),
            enforcement_mode=raw["enforcement_mode"],
            executed=raw["executed"],
            record_type=raw["record_type"],
            references_hash=raw["references_hash"],
            human_approver=raw["human_approver"],
            approval_reason=raw["approval_reason"],
            created_at=raw["created_at"],
            record_hash=raw["record_hash"],
            prev_hash=raw["prev_hash"],
        )

    def _ensure_table(self) -> None:
        if self._uses_sqlite:
            with self._sqlite_connection() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        correlation_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        context_used TEXT NOT NULL,
                        evidence TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        enforcement_mode TEXT NOT NULL,
                        executed INTEGER NOT NULL,
                        record_type TEXT NOT NULL,
                        references_hash TEXT,
                        human_approver TEXT,
                        approval_reason TEXT,
                        created_at TEXT NOT NULL,
                        record_hash TEXT NOT NULL,
                        prev_hash TEXT NOT NULL
                    )
                    """
                )
            return

        with self._postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_records (
                        id bigserial PRIMARY KEY,
                        correlation_id text NOT NULL,
                        action jsonb NOT NULL,
                        context_used jsonb NOT NULL,
                        evidence jsonb NOT NULL,
                        decision jsonb NOT NULL,
                        enforcement_mode text NOT NULL,
                        executed boolean NOT NULL,
                        record_type text NOT NULL,
                        references_hash text,
                        human_approver text,
                        approval_reason text,
                        created_at timestamptz NOT NULL,
                        record_hash text NOT NULL,
                        prev_hash text NOT NULL
                    )
                    """
                )

    def _insert_row(
        self,
        *,
        correlation_id: UUID,
        action_payload: dict[str, Any],
        context_payload: dict[str, Any],
        evidence_payload: dict[str, Any],
        decision_payload: dict[str, Any],
        enforcement_mode: str,
        executed: bool,
        record_type: str,
        references_hash: str | None,
        human_approver: str | None,
        approval_reason: str | None,
        created_at: datetime,
        record_hash: str,
        prev_hash: str,
    ) -> int:
        if self._uses_sqlite:
            with self._sqlite_connection() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO audit_records (
                        correlation_id, action, context_used, evidence, decision,
                        enforcement_mode, executed, record_type, references_hash,
                        human_approver, approval_reason, created_at, record_hash, prev_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(correlation_id),
                        json.dumps(action_payload, sort_keys=True),
                        json.dumps(context_payload, sort_keys=True),
                        json.dumps(evidence_payload, sort_keys=True),
                        json.dumps(decision_payload, sort_keys=True),
                        enforcement_mode,
                        int(executed),
                        record_type,
                        references_hash,
                        human_approver,
                        approval_reason,
                        created_at.isoformat(),
                        record_hash,
                        prev_hash,
                    ),
                )
                return int(cursor.lastrowid)

        with self._postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_records (
                        correlation_id, action, context_used, evidence, decision,
                        enforcement_mode, executed, record_type, references_hash,
                        human_approver, approval_reason, created_at, record_hash, prev_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        str(correlation_id),
                        Jsonb(action_payload),
                        Jsonb(context_payload),
                        Jsonb(evidence_payload),
                        Jsonb(decision_payload),
                        enforcement_mode,
                        executed,
                        record_type,
                        references_hash,
                        human_approver,
                        approval_reason,
                        created_at,
                        record_hash,
                        prev_hash,
                    ),
                )
                return int(cursor.fetchone()[0])

    def _fetch_all_rows(self) -> list[dict[str, Any]]:
        if self._uses_sqlite:
            with self._sqlite_connection() as connection:
                rows = connection.execute(
                    """
                    SELECT id, correlation_id, action, context_used, evidence, decision,
                           enforcement_mode, executed, record_type, references_hash,
                           human_approver, approval_reason, created_at, record_hash, prev_hash
                    FROM audit_records ORDER BY id ASC
                    """
                ).fetchall()
                return [self._sqlite_row_to_dict(row) for row in rows]

        with self._postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, correlation_id, action, context_used, evidence, decision,
                           enforcement_mode, executed, record_type, references_hash,
                           human_approver, approval_reason, created_at, record_hash, prev_hash
                    FROM audit_records ORDER BY id ASC
                    """
                )
                rows = cursor.fetchall()
                return [self._postgres_row_to_dict(row) for row in rows]

    def _fetch_row(self, record_id: int) -> dict[str, Any]:
        for row in self._fetch_all_rows():
            if row["id"] == record_id:
                return row
        raise ValueError(f"no audit record with id {record_id}")

    def _update_executed(self, record_id: int, executed: bool) -> None:
        if self._uses_sqlite:
            with self._sqlite_connection() as connection:
                connection.execute(
                    "UPDATE audit_records SET executed = ? WHERE id = ?",
                    (int(executed), record_id),
                )
            return

        with self._postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE audit_records SET executed = %s WHERE id = %s",
                    (executed, record_id),
                )

    @staticmethod
    def _sqlite_row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
        (
            id_,
            correlation_id,
            action,
            context_used,
            evidence,
            decision,
            enforcement_mode,
            executed,
            record_type,
            references_hash,
            human_approver,
            approval_reason,
            created_at,
            record_hash,
            prev_hash,
        ) = row
        return {
            "id": int(id_),
            "correlation_id": UUID(correlation_id),
            "action": json.loads(action),
            "context_used": json.loads(context_used),
            "evidence": json.loads(evidence),
            "decision": json.loads(decision),
            "enforcement_mode": enforcement_mode,
            "executed": bool(executed),
            "record_type": record_type,
            "references_hash": references_hash,
            "human_approver": human_approver,
            "approval_reason": approval_reason,
            "created_at": datetime.fromisoformat(created_at),
            "record_hash": record_hash,
            "prev_hash": prev_hash,
        }

    @staticmethod
    def _postgres_row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
        (
            id_,
            correlation_id,
            action,
            context_used,
            evidence,
            decision,
            enforcement_mode,
            executed,
            record_type,
            references_hash,
            human_approver,
            approval_reason,
            created_at,
            record_hash,
            prev_hash,
        ) = row
        return {
            "id": int(id_),
            "correlation_id": UUID(correlation_id),
            "action": action,
            "context_used": context_used,
            "evidence": evidence,
            "decision": decision,
            "enforcement_mode": enforcement_mode,
            "executed": bool(executed),
            "record_type": record_type,
            "references_hash": references_hash,
            "human_approver": human_approver,
            "approval_reason": approval_reason,
            "created_at": created_at,
            "record_hash": record_hash,
            "prev_hash": prev_hash,
        }

    def _sqlite_connection(self) -> sqlite3.Connection:
        assert self.database_url is not None
        return sqlite3.connect(self.database_url.removeprefix("sqlite:///"))

    def _postgres_connection(self) -> psycopg.Connection[Any]:
        if self.database_url:
            return psycopg.connect(self.database_url)
        return psycopg.connect(**get_settings().postgres_connection_kwargs)


def get_audit_store() -> AuditStore:
    """Factory used by later pipeline tasks to load the authoritative audit store."""

    return AuditStore()
