from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from app.models import AccessContext, AuditEvent


class AuditStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS access_audit (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    target TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL
                )
                """
            )

    def record(
        self,
        context: AccessContext,
        operation: str,
        target: str,
        allowed: bool,
        reason: str,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=uuid4().hex,
            requester_id=context.requester_id,
            role=context.role,
            purpose=context.purpose,
            operation=operation,
            target=target,
            decision="allow" if allowed else "deny",
            reason=reason,
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO access_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.requester_id,
                    event.role.value,
                    event.purpose.value,
                    event.operation,
                    event.target,
                    event.decision,
                    event.reason,
                ),
            )
        return event

    def count(self, decision: str | None = None) -> int:
        query = "SELECT COUNT(*) AS count FROM access_audit"
        args: tuple[str, ...] = ()
        if decision:
            query += " WHERE decision = ?"
            args = (decision,)
        with self._connect() as connection:
            row = connection.execute(query, args).fetchone()
        return int(row["count"])

