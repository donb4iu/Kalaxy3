"""Shared SAGE evidence catalog, template, and compatibility authorities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .markdown import MarkdownDocument, require_inside, unique_strings
from .model import WorkflowError

DEFAULT_TEMPLATE_POLICY = Path("sage-evidence-template-policy.json")


@dataclass(frozen=True)
class EvidenceRecord:
    """Normalized evidence-catalog record used by docs and guardrails."""

    evidence_id: str
    source_path: str
    record_class: str
    title: str
    nav_title: str
    metadata_source: str
    migration_status: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvidenceRecord":
        """Validate and normalize one catalog mapping."""
        required = (
            "evidence_id",
            "source_path",
            "record_class",
            "title",
            "nav_title",
            "metadata_source",
            "migration_status",
        )
        missing = [key for key in required if not isinstance(value.get(key), str)]
        if missing:
            raise WorkflowError(f"Catalog record fields are missing: {missing}")
        return cls(*(str(value[key]) for key in required))

    def staged_source_path(self, prefix: str = "markdown/") -> str:
        """Return the staged-source path for this repository record."""
        if not self.source_path.startswith(prefix):
            raise WorkflowError(
                f"Evidence source path lacks {prefix!r}: {self.source_path}"
            )
        return self.source_path[len(prefix) :]


@dataclass(frozen=True)
class EvidenceCatalog:
    """Validated immutable view of the generated evidence catalog."""

    path: Path
    records: tuple[EvidenceRecord, ...]
    fingerprint: str | None

    @classmethod
    def load(cls, path: Path) -> "EvidenceCatalog":
        """Load and validate one generated evidence catalog."""
        resolved = path.expanduser().resolve()
        if not resolved.is_file():
            raise WorkflowError(f"Evidence catalog is missing: {resolved}")
        payload = json.loads(resolved.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise WorkflowError("Evidence catalog must be a JSON object")
        values = payload.get("records")
        if not isinstance(values, list):
            raise WorkflowError("Evidence catalog records must be an array")
        records = tuple(EvidenceRecord.from_mapping(item) for item in values)
        identifiers = [item.evidence_id for item in records]
        if len(identifiers) != len(set(identifiers)):
            raise WorkflowError("Evidence catalog contains duplicate IDs")
        fingerprint = payload.get("catalog_fingerprint")
        if fingerprint is not None and not isinstance(fingerprint, str):
            raise WorkflowError("Catalog fingerprint must be a string or null")
        return cls(resolved, records, fingerprint)

    def current(self, record_class: str) -> tuple[EvidenceRecord, ...]:
        """Return records matching the declared current class."""
        return tuple(item for item in self.records if item.record_class == record_class)

    def legacy(self, record_class: str) -> tuple[EvidenceRecord, ...]:
        """Return records outside the declared current class."""
        return tuple(item for item in self.records if item.record_class != record_class)

    def staged_paths(self, prefix: str = "markdown/") -> set[str]:
        """Return staged-source paths for every cataloged record."""
        return {item.staged_source_path(prefix) for item in self.records}


@dataclass(frozen=True)
class EvidenceTemplatePolicy:
    """Machine-readable compatibility and authority-path policy."""

    path: Path
    metadata_contract_path: str
    template_path: str
    catalog_path: str
    publisher_path: str
    current_record_class: str
    immutable_record_classes: tuple[str, ...]
    compatible_heading_prefixes: tuple[str, ...]
    exact_template_required_for_new_packages: bool

    @classmethod
    def load(cls, path: Path) -> "EvidenceTemplatePolicy":
        """Load and validate the evidence-template policy."""
        resolved = path.expanduser().resolve()
        payload = json.loads(resolved.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise WorkflowError("Evidence template policy must be an object")
        immutable = payload.get("immutable_record_classes")
        prefixes = payload.get("compatible_heading_prefixes")
        if not isinstance(immutable, list) or not isinstance(prefixes, list):
            raise WorkflowError("Evidence template policy arrays are missing")
        strings = (
            "metadata_contract_path",
            "template_path",
            "catalog_path",
            "publisher_path",
            "current_record_class",
        )
        for key in strings:
            if not isinstance(payload.get(key), str) or not payload[key]:
                raise WorkflowError(f"Evidence template policy field missing: {key}")
        exact = payload.get("exact_template_required_for_new_packages")
        if exact is not True:
            raise WorkflowError("New evidence packages must require exact template")
        return cls(
            resolved,
            *(str(payload[key]) for key in strings),
            unique_strings(str(item) for item in immutable),
            unique_strings(str(item) for item in prefixes),
            exact,
        )


@dataclass(frozen=True)
class EvidenceAuthorities:
    """Resolved contract, template, catalog, and compatibility authorities."""

    repository_root: Path
    policy: EvidenceTemplatePolicy
    contract: Mapping[str, Any]
    template: MarkdownDocument
    catalog: EvidenceCatalog

    @classmethod
    def load(
        cls,
        repository_root: Path,
        policy_path: Path = DEFAULT_TEMPLATE_POLICY,
    ) -> "EvidenceAuthorities":
        """Load all evidence authorities from one repository root."""
        root = repository_root.expanduser().resolve()
        policy = EvidenceTemplatePolicy.load(require_inside(root, policy_path))
        contract_path = require_inside(root, Path(policy.metadata_contract_path))
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        if not isinstance(contract, dict):
            raise WorkflowError("Evidence metadata contract must be an object")
        template = MarkdownDocument.load(
            require_inside(root, Path(policy.template_path))
        )
        catalog = EvidenceCatalog.load(
            require_inside(root, Path(policy.catalog_path))
        )
        return cls(root, policy, contract, template, catalog)

    @property
    def front_matter_order(self) -> tuple[str, ...]:
        """Return canonical front-matter order from the JSON contract."""
        values = self.contract.get("front_matter_order")
        if not isinstance(values, list):
            raise WorkflowError("Contract front_matter_order must be an array")
        return unique_strings(str(item) for item in values)

    @property
    def list_fields(self) -> tuple[str, ...]:
        """Return canonical list fields from the JSON contract."""
        values = self.contract.get("list_fields")
        if not isinstance(values, list):
            raise WorkflowError("Contract list_fields must be an array")
        return unique_strings(str(item) for item in values)

    @property
    def metadata_rows(self) -> tuple[tuple[str, str], ...]:
        """Return canonical static metadata rows."""
        values = self.contract.get("static_metadata_rows")
        if not isinstance(values, list):
            raise WorkflowError("Contract metadata rows must be an array")
        rows: list[tuple[str, str]] = []
        for item in values:
            if not isinstance(item, list) or len(item) != 2:
                raise WorkflowError("Metadata row must contain label and key")
            rows.append((str(item[0]), str(item[1])))
        return tuple(rows)

    @property
    def five_w_rows(self) -> tuple[str, ...]:
        """Return canonical Five-W-and-How row labels."""
        values = self.contract.get("five_w_rows")
        if not isinstance(values, list):
            raise WorkflowError("Contract five_w_rows must be an array")
        return unique_strings(str(item) for item in values)

    @property
    def template_headings(self) -> tuple[str, ...]:
        """Return exact current-template H2 headings."""
        return self.template.h2_headings()

    def authority_summary(self) -> dict[str, Any]:
        """Return a stable machine-readable authority summary."""
        return {
            "front_matter_fields": len(self.front_matter_order),
            "list_fields": len(self.list_fields),
            "metadata_rows": len(self.metadata_rows),
            "five_w_rows": list(self.five_w_rows),
            "template_headings": list(self.template_headings),
            "catalog_records": len(self.catalog.records),
        }

    def compatible_headings(self, headings: Sequence[str]) -> bool:
        """Return whether headings preserve the immutable compatibility order."""
        position = -1
        for prefix in self.policy.compatible_heading_prefixes:
            found = next(
                (
                    index
                    for index in range(position + 1, len(headings))
                    if headings[index].startswith(prefix)
                ),
                None,
            )
            if found is None:
                return False
            position = found
        return True

    def classify_current_record(self, record: EvidenceRecord) -> str:
        """Classify one current record as exact or immutable-compatible."""
        path = require_inside(self.repository_root, Path(record.source_path))
        document = MarkdownDocument.load(path)
        if document.front_matter_keys() != self.front_matter_order:
            raise WorkflowError(f"Current front matter differs: {record.source_path}")
        if "[TOC]" not in document.body:
            raise WorkflowError(f"Current record lacks TOC: {record.source_path}")
        headings = document.h2_headings()
        if headings == self.template_headings:
            return "exact-current-template"
        if self.compatible_headings(headings):
            return "compatible-immutable-variant"
        raise WorkflowError(f"Current section contract differs: {record.source_path}")


def default_repository_root() -> Path:
    """Return the repository root containing this installed workflow module."""
    return Path(__file__).resolve().parents[3]


def load_publication_authorities() -> EvidenceAuthorities:
    """Load publication authorities for the installed repository."""
    return EvidenceAuthorities.load(default_repository_root())


PUBLICATION_AUTHORITIES = load_publication_authorities()
REQUIRED_FRONTMATTER_ORDER = list(PUBLICATION_AUTHORITIES.front_matter_order)
REQUIRED_FRONTMATTER = REQUIRED_FRONTMATTER_ORDER
LIST_FIELDS = set(PUBLICATION_AUTHORITIES.list_fields)
STATIC_METADATA_ROWS = list(PUBLICATION_AUTHORITIES.metadata_rows)
FIVE_W_ROWS = list(PUBLICATION_AUTHORITIES.five_w_rows)
REQUIRED_TEMPLATE_HEADINGS = list(PUBLICATION_AUTHORITIES.template_headings)
