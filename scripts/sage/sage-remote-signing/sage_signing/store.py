"""Durable one-time signing intent ledger; not the governed audit evidence store."""

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, NamedTuple


class Intent(NamedTuple):
    """One ephemeral, exactly-bound signing request."""

    intent_id: str
    subject: str
    digest: str
    data: bytes
    purpose: str
    created_at: int


class IntentStore:
    """Use SQLite atomic state transitions to reject repeat signing."""

    def __init__(self, database: Path) -> None:
        """Create a durable ledger at the configured private volume path.

        Args:
            database: SQLite location on the persistent state volume.
        """
        database.parent.mkdir(parents=True, exist_ok=True)
        self.database = database
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS intents ("
                "id TEXT PRIMARY KEY, subject TEXT NOT NULL, digest TEXT NOT NULL, "
                "data BLOB NOT NULL, purpose TEXT NOT NULL, created_at INTEGER NOT NULL, "
                "state TEXT NOT NULL)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Commit and close an SQLite connection on context exit."""
        connection = sqlite3.connect(self.database, timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def stage(self, intent: Intent) -> None:
        """Persist one pending request without authorizing a signature.

        Args:
            intent: Digest, bytes, context, and authenticated requester.
        """
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM intents WHERE created_at < ?",
                (int(time.time()) - 600,),
            )
            count = connection.execute(
                "SELECT COUNT(*) FROM intents WHERE subject=? AND state='pending'",
                (intent.subject,),
            ).fetchone()[0]
            if count >= 20:
                raise PermissionError("Too many pending signing intents")
            connection.execute(
                "INSERT INTO intents VALUES (?, ?, ?, ?, ?, ?, 'pending')",
                tuple(intent),
            )

    def consume(self, intent_id: str, subject: str, digest: str) -> Intent:
        """Atomically consume a matching unexpired intent before signing.

        Args:
            intent_id: Opaque request identifier.
            subject: Verified Cloudflare identity.
            digest: Operator-confirmed SHA-256 digest.
        """
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT id, subject, digest, data, purpose, created_at "
                "FROM intents WHERE id=? AND state='pending'", (intent_id,),
            ).fetchone()
            if not row or row[1] != subject or row[2] != digest:
                raise PermissionError("Intent not authorized or already consumed")
            intent = Intent(*row)
            if int(time.time()) - intent.created_at > 300:
                raise PermissionError("Intent expired")
            connection.execute(
                "UPDATE intents SET state='consumed', data=X'' WHERE id=?", (intent_id,),
            )
            return intent
