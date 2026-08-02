"""Reusable Markdown and repository-path parsing for SAGE workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import WorkflowError

_TOP_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s|$)")
_SCALAR = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*?)\s*$")
_H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_TABLE_LABEL = re.compile(r"^\|\s*\*\*(.+?)\*\*\s*\|", re.MULTILINE)


@dataclass(frozen=True)
class MarkdownDocument:
    """Parsed Markdown with YAML-like front matter and heading helpers."""

    path: Path
    text: str
    front_matter: tuple[str, ...]
    body: str

    @classmethod
    def load(cls, path: Path) -> "MarkdownDocument":
        """Load and parse one UTF-8 Markdown document."""
        resolved = path.expanduser().resolve()
        if not resolved.is_file():
            raise WorkflowError(f"Markdown document is missing: {resolved}")
        return cls.parse(resolved, resolved.read_text(encoding="utf-8"))

    @classmethod
    def parse(cls, path: Path, text: str) -> "MarkdownDocument":
        """Parse one Markdown document from supplied text."""
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            return cls(path, text, tuple(), text)
        try:
            end = lines.index("---", 1)
        except ValueError as error:
            raise WorkflowError(
                f"Closing front matter is missing: {path}"
            ) from error
        front = tuple(lines[1:end])
        body = "\n".join(lines[end + 1 :])
        return cls(path, text, front, body)

    def require_front_matter(self) -> None:
        """Require the document to contain front matter."""
        if not self.front_matter:
            raise WorkflowError(
                f"Opening front matter is missing: {self.path}"
            )

    def front_matter_keys(self) -> tuple[str, ...]:
        """Return top-level front-matter keys in source order."""
        self.require_front_matter()
        keys: list[str] = []
        for line in self.front_matter:
            match = _TOP_KEY.match(line)
            if match:
                keys.append(match.group(1))
        return tuple(keys)

    def scalar(self, key: str) -> str | None:
        """Return one simple top-level scalar front-matter value."""
        for line in self.front_matter:
            match = _SCALAR.fullmatch(line)
            if match and match.group(1) == key:
                return match.group(2).strip().strip("'\"")
        return None

    def first_h1(self) -> str | None:
        """Return the first H1 heading, normalized for display."""
        match = _H1.search(self.body)
        return " ".join(match.group(1).split()) if match else None

    def h2_headings(self) -> tuple[str, ...]:
        """Return H2 headings in source order."""
        return tuple(match.group(1).strip() for match in _H2.finditer(self.body))

    def table_labels(self, section_heading: str) -> tuple[str, ...]:
        """Return bold first-column labels from one H2 section table."""
        marker = f"## {section_heading}"
        if marker not in self.body:
            raise WorkflowError(
                f"Section {section_heading!r} is missing: {self.path}"
            )
        section = self.body.split(marker, 1)[1].split("\n## ", 1)[0]
        return tuple(match.group(1).strip() for match in _TABLE_LABEL.finditer(section))


def require_inside(root: Path, path: Path) -> Path:
    """Resolve a path and require it to remain inside the declared root."""
    resolved_root = root.expanduser().resolve()
    raw = path.expanduser()
    resolved = raw.resolve() if raw.is_absolute() else (resolved_root / raw).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise WorkflowError(f"Path escapes declared root: {resolved}")
    return resolved


def unique_strings(values: Iterable[str]) -> tuple[str, ...]:
    """Return non-empty strings in stable first-seen order."""
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return tuple(result)
