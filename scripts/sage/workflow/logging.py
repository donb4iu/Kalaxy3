"""Append-only structured event logging with secret-safe fields."""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

_SECRET_PATTERNS = (
    re.compile(r"(?i)(password|passwd|token|secret|api[_-]?key)=([^\s]+)"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)([^\s]+)"),
)


def utc_timestamp() -> str:
    """Return an ISO-8601 timestamp with timezone."""

    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def digest_parts(values: Iterable[str]) -> str:
    """Return a deterministic digest without retaining raw values."""

    payload = "\x1f".join(values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def redact_text(
    value: str,
    sensitive_values: Iterable[str] = (),
) -> str:
    """Redact explicit and common secret-bearing values."""

    result = value
    for secret in sensitive_values:
        if secret:
            result = result.replace(secret, "[REDACTED]")
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(
            lambda match: (
                f"{match.group(1)}=[REDACTED]"
                if "=" in match.group(0)
                else f"{match.group(1)}[REDACTED]"
            ),
            result,
        )
    return result


class JsonlEventLogger:
    """Write fsync-backed JSONL events without raw commands or output."""

    def __init__(
        self,
        path: Path,
        workflow_id: str,
        *,
        primitive_versions: Mapping[str, str] | None = None,
    ) -> None:
        self.path = path
        self.workflow_id = workflow_id
        self.primitive_versions = dict(primitive_versions or {})
        self._sequence = 0
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        *,
        event: str,
        status: str,
        primitive_id: str,
        step_id: str | None = None,
        fields: Mapping[str, Any] | None = None,
    ) -> None:
        """Append one normalized workflow event."""

        with self._lock:
            self._sequence += 1
            payload: dict[str, Any] = {
                "schema_version": "1.0",
                "timestamp": utc_timestamp(),
                "workflow_id": self.workflow_id,
                "sequence": self._sequence,
                "event": event,
                "status": status,
                "primitive_id": primitive_id,
                "primitive_version": self.primitive_versions.get(
                    primitive_id
                ),
                "step_id": step_id,
            }
            if fields:
                payload.update(dict(fields))

            encoded = (
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            ).encode("utf-8")

            descriptor = os.open(
                self.path,
                os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                0o600,
            )
            try:
                os.write(descriptor, encoded)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
