"""Atomic workflow closeout evidence with primitive-version provenance."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from .catalog import PrimitiveCatalog


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


class CloseoutWriter:
    """Write fsync-backed atomic JSON closeout evidence."""

    def __init__(
        self,
        *,
        destination_directory: Path,
        primitive_registry: Path,
        event_log: Path,
    ) -> None:
        self.destination_directory = (
            destination_directory.expanduser().resolve()
        )
        self.primitive_registry = primitive_registry.expanduser().resolve()
        self.event_log = event_log.expanduser().resolve()

    def write(
        self,
        *,
        workflow_id: str,
        status: str,
        used_primitives: Iterable[str],
        details: Mapping[str, Any],
    ) -> Path:
        self.destination_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        catalog = PrimitiveCatalog.load(self.primitive_registry)
        primitive_versions = catalog.versions_for(used_primitives)
        payload = {
            "schema_version": "1.0",
            "record_type": "sage-workflow-closeout",
            "captured_at": (
                datetime.now()
                .astimezone()
                .isoformat(timespec="seconds")
            ),
            "workflow_id": workflow_id,
            "status": status,
            "framework_version": catalog.framework_version,
            "primitive_versions": primitive_versions,
            "event_log": {
                "path": str(self.event_log),
                "sha256": (
                    file_sha256(self.event_log)
                    if self.event_log.is_file()
                    else None
                ),
            },
            "details": dict(details),
        }

        name = (
            f"{workflow_id}-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".json"
        )
        destination = self.destination_directory / name
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{name}.",
            suffix=".tmp",
            dir=self.destination_directory,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=4)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
            directory_descriptor = os.open(
                self.destination_directory,
                os.O_RDONLY,
            )
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        finally:
            if temporary.exists():
                temporary.unlink()
        return destination
