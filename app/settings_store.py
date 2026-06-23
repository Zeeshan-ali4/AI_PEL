"""DB-backed runtime settings store for the policy gate.

T08 owns the single authoritative settings row used by later pipeline and OPA
integration tasks.  The store keeps runtime configuration only: it does not make
policy decisions, evaluate scenarios, or encode allow/block/escalate logic.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Literal

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import get_settings

EnforcementMode = Literal["shadow", "soft", "full"]
VALID_ENFORCEMENT_MODES: set[str] = {"shadow", "soft", "full"}
DEFAULT_HIGH_CONFIDENCE_THRESHOLD = 0.75
SETTINGS_ROW_ID = 1

# Spec §6 control IDs.  T09 will add richer metadata in controls.json; T08 only
# stores the runtime mode selected for each control.
DEFAULT_CONTROL_MODES: dict[str, EnforcementMode] = {
    "FIN-PAY-001": "shadow",
    "FIN-PAY-002": "shadow",
    "FIN-PAY-003": "shadow",
    "FIN-PAY-004": "shadow",
    "COMM-EMAIL-001": "shadow",
    "COMM-EMAIL-002": "shadow",
    "COMM-EMAIL-003": "shadow",
}


class RuntimeSettings(BaseModel):
    """Runtime-editable settings loaded before policy decisioning."""

    high_confidence_threshold: float = Field(ge=0.0, le=1.0)
    control_modes: dict[str, EnforcementMode]

    model_config = ConfigDict(frozen=True)

    @field_validator("control_modes")
    @classmethod
    def validate_control_modes(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError("control_modes must contain at least one control mode")
        invalid = {control_id: mode for control_id, mode in value.items() if mode not in VALID_ENFORCEMENT_MODES}
        if invalid:
            raise ValueError(f"control modes must be one of {sorted(VALID_ENFORCEMENT_MODES)}: {invalid}")
        return value

    def to_policy_config(self) -> dict[str, Any]:
        """Return the config shape later OPA/pipeline code can embed under input.config."""

        return {
            "high_confidence_threshold": self.high_confidence_threshold,
            "control_modes": dict(self.control_modes),
        }


@dataclass(frozen=True)
class SettingsStore:
    """One-row persistent settings store.

    Default construction connects to Postgres using ``app.config``.  Tests may
    pass a ``sqlite:///`` URL to exercise the same persistence semantics using
    an on-disk database without Docker.
    """

    database_url: str | None = None

    def read_settings(self) -> RuntimeSettings:
        """Read the singleton settings row, seeding defaults on first use."""

        self._ensure_table()
        settings = self._fetch_settings()
        if settings is None:
            settings = RuntimeSettings(
                high_confidence_threshold=DEFAULT_HIGH_CONFIDENCE_THRESHOLD,
                control_modes=dict(DEFAULT_CONTROL_MODES),
            )
            self._insert_settings(settings)
        return settings

    def update_threshold(self, threshold: float) -> RuntimeSettings:
        """Persist a new high-confidence threshold and return the updated row."""

        current = self.read_settings()
        updated = RuntimeSettings(
            high_confidence_threshold=threshold,
            control_modes=dict(current.control_modes),
        )
        self._update_settings(updated)
        return updated

    def update_control_mode(self, control_id: str, mode: EnforcementMode) -> RuntimeSettings:
        """Persist one per-control enforcement mode and return the updated row."""

        current = self.read_settings()
        control_modes = dict(current.control_modes)
        control_modes[control_id] = mode
        updated = RuntimeSettings(
            high_confidence_threshold=current.high_confidence_threshold,
            control_modes=control_modes,
        )
        self._update_settings(updated)
        return updated

    def update_control_modes(self, control_modes: dict[str, EnforcementMode]) -> RuntimeSettings:
        """Persist a complete per-control mode mapping and return the updated row."""

        current = self.read_settings()
        updated = RuntimeSettings(
            high_confidence_threshold=current.high_confidence_threshold,
            control_modes=dict(control_modes),
        )
        self._update_settings(updated)
        return updated

    def row_count(self) -> int:
        """Return the number of settings rows for reviewer/test visibility."""

        self._ensure_table()
        if self._uses_sqlite:
            with self._sqlite_connection() as connection:
                return int(connection.execute("SELECT COUNT(*) FROM runtime_settings").fetchone()[0])
        with self._postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM runtime_settings")
                return int(cursor.fetchone()[0])

    @property
    def _uses_sqlite(self) -> bool:
        return bool(self.database_url and self.database_url.startswith("sqlite:///"))

    def _ensure_table(self) -> None:
        if self._uses_sqlite:
            with self._sqlite_connection() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS runtime_settings (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        high_confidence_threshold REAL NOT NULL CHECK (high_confidence_threshold >= 0 AND high_confidence_threshold <= 1),
                        control_modes TEXT NOT NULL,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            return

        with self._postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS runtime_settings (
                        id integer PRIMARY KEY CHECK (id = 1),
                        high_confidence_threshold double precision NOT NULL CHECK (high_confidence_threshold >= 0 AND high_confidence_threshold <= 1),
                        control_modes jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )

    def _fetch_settings(self) -> RuntimeSettings | None:
        if self._uses_sqlite:
            with self._sqlite_connection() as connection:
                row = connection.execute(
                    "SELECT high_confidence_threshold, control_modes FROM runtime_settings WHERE id = ?",
                    (SETTINGS_ROW_ID,),
                ).fetchone()
                if row is None:
                    return None
                return RuntimeSettings(high_confidence_threshold=row[0], control_modes=json.loads(row[1]))

        with self._postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT high_confidence_threshold, control_modes FROM runtime_settings WHERE id = %s",
                    (SETTINGS_ROW_ID,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return RuntimeSettings(high_confidence_threshold=row[0], control_modes=row[1])

    def _insert_settings(self, settings: RuntimeSettings) -> None:
        if self._uses_sqlite:
            with self._sqlite_connection() as connection:
                connection.execute(
                    "INSERT INTO runtime_settings (id, high_confidence_threshold, control_modes) VALUES (?, ?, ?)",
                    (SETTINGS_ROW_ID, settings.high_confidence_threshold, json.dumps(settings.control_modes, sort_keys=True)),
                )
            return

        with self._postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO runtime_settings (id, high_confidence_threshold, control_modes) VALUES (%s, %s, %s)",
                    (SETTINGS_ROW_ID, settings.high_confidence_threshold, Jsonb(settings.control_modes)),
                )

    def _update_settings(self, settings: RuntimeSettings) -> None:
        if self._uses_sqlite:
            with self._sqlite_connection() as connection:
                connection.execute(
                    """
                    UPDATE runtime_settings
                    SET high_confidence_threshold = ?, control_modes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (settings.high_confidence_threshold, json.dumps(settings.control_modes, sort_keys=True), SETTINGS_ROW_ID),
                )
            return

        with self._postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE runtime_settings
                    SET high_confidence_threshold = %s, control_modes = %s, updated_at = now()
                    WHERE id = %s
                    """,
                    (settings.high_confidence_threshold, Jsonb(settings.control_modes), SETTINGS_ROW_ID),
                )

    def _sqlite_connection(self) -> sqlite3.Connection:
        assert self.database_url is not None
        return sqlite3.connect(self.database_url.removeprefix("sqlite:///"))

    def _postgres_connection(self) -> psycopg.Connection[Any]:
        if self.database_url:
            return psycopg.connect(self.database_url)
        return psycopg.connect(**get_settings().postgres_connection_kwargs)


def get_settings_store() -> SettingsStore:
    """Factory used by later tasks to load the authoritative runtime settings row."""

    return SettingsStore()
