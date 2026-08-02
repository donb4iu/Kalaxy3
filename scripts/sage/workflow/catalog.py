"""Versioned primitive catalog and maturity metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .model import WorkflowError


class PrimitiveCatalog:
    """Load and validate the repository-owned primitive registry."""

    def __init__(
        self,
        *,
        framework_version: str,
        primitives: Mapping[str, Mapping[str, Any]],
    ) -> None:
        self.framework_version = framework_version
        self.primitives = dict(primitives)

    @classmethod
    def load(cls, path: Path) -> "PrimitiveCatalog":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise WorkflowError("Primitive registry must be a JSON object")
        framework_version = payload.get("framework_version")
        if not isinstance(framework_version, str):
            raise WorkflowError("Primitive registry framework_version is missing")

        entries = payload.get("primitives")
        if not isinstance(entries, list):
            raise WorkflowError("Primitive registry primitives must be an array")

        primitives: dict[str, Mapping[str, Any]] = {}
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise WorkflowError(
                    f"Primitive registry entry {index} must be an object"
                )
            primitive_id = entry.get("primitive_id")
            version = entry.get("version")
            if not isinstance(primitive_id, str) or not primitive_id:
                raise WorkflowError(
                    f"Primitive registry entry {index} has no primitive_id"
                )
            if not isinstance(version, str) or not version:
                raise WorkflowError(
                    f"Primitive {primitive_id} has no version"
                )
            if primitive_id in primitives:
                raise WorkflowError(
                    f"Duplicate primitive identifier: {primitive_id}"
                )
            primitives[primitive_id] = entry

        return cls(
            framework_version=framework_version,
            primitives=primitives,
        )

    def require(self, primitive_ids: Iterable[str]) -> tuple[str, ...]:
        identifiers = tuple(dict.fromkeys(primitive_ids))
        unknown = sorted(
            primitive_id
            for primitive_id in identifiers
            if primitive_id not in self.primitives
        )
        if unknown:
            raise WorkflowError(
                f"Unknown workflow primitives: {unknown}"
            )
        return identifiers

    def versions_for(
        self,
        primitive_ids: Iterable[str],
    ) -> dict[str, str]:
        identifiers = self.require(primitive_ids)
        return {
            primitive_id: str(
                self.primitives[primitive_id]["version"]
            )
            for primitive_id in identifiers
        }

    def maturity_for(self, primitive_id: str) -> str:
        self.require((primitive_id,))
        return str(
            self.primitives[primitive_id].get("maturity", "unknown")
        )
