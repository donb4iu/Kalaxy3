"""Shared policy-driven MkDocs navigation generation and parsing support."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urljoin, urlparse

SAGE_ROOT = Path(__file__).resolve().parents[1] / "sage"
if str(SAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(SAGE_ROOT))

from workflow.evidence_records import EvidenceCatalog  # noqa: E402
from workflow.markdown import MarkdownDocument, require_inside  # noqa: E402
from workflow.model import WorkflowError  # noqa: E402

_NUMBER_PREFIX = re.compile(r"^(\d+)[-_ ]*(.*)$")


class NavigationError(WorkflowError):
    """Raised when the MkDocs navigation contract cannot be satisfied."""


@dataclass(frozen=True)
class CuratedPage:
    """One policy-declared primary navigation page."""

    label: str
    path: str


@dataclass(frozen=True)
class NavigationPolicy:
    """Validated machine-readable primary-navigation policy."""

    path: Path
    root_label: str
    landing_page: str
    excluded_top_level_names: tuple[str, ...]
    label_front_matter_key: str
    maximum_label_length: int
    evidence_root: str
    evidence_label: str
    evidence_index_page: str
    evidence_catalog_path: str
    evidence_source_prefix: str
    hidden_evidence_groups: tuple[str, ...]
    curated_evidence_pages: tuple[CuratedPage, ...]
    material_primary_classes: frozenset[str]
    material_secondary_classes: frozenset[str]
    material_leaf_class: str

    @classmethod
    def load(cls, path: Path) -> "NavigationPolicy":
        """Load and validate one navigation policy JSON file."""
        resolved = path.expanduser().resolve()
        payload = json.loads(resolved.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise NavigationError("Navigation policy must be a JSON object")
        label = require_mapping(payload, "label_policy")
        evidence = require_mapping(payload, "evidence")
        material = require_mapping(payload, "material")
        pages = require_curated_pages(evidence.get("curated_pages"))
        maximum = label.get("maximum_length")
        if not isinstance(maximum, int) or not 1 <= maximum <= 200:
            raise NavigationError("Navigation label maximum is invalid")
        return cls(
            resolved,
            require_string(payload, "site_root_label"),
            require_string(payload, "landing_page"),
            require_strings(payload, "excluded_top_level_names"),
            require_string(label, "front_matter_key"),
            maximum,
            require_string(evidence, "root_directory"),
            require_string(evidence, "root_label"),
            require_string(evidence, "index_page"),
            require_string(evidence, "catalog_path"),
            require_string(evidence, "repository_source_prefix"),
            require_strings(evidence, "hide_generated_group_children"),
            pages,
            frozenset(require_strings(material, "primary_navigation_classes")),
            frozenset(require_strings(material, "secondary_navigation_classes")),
            require_string(material, "leaf_link_class"),
        )

    def as_manifest(self) -> dict[str, Any]:
        """Return stable policy details used by generated manifests."""
        return {
            "policy_path": self.path.name,
            "root_label": self.root_label,
            "maximum_label_length": self.maximum_label_length,
            "evidence_index": {
                "label": self.evidence_label,
                "path": self.evidence_index_page,
            },
            "curated_evidence": [
                {"label": item.label, "path": item.path}
                for item in self.curated_evidence_pages
            ],
        }


def primary_evidence_pages(
    policy: NavigationPolicy,
) -> tuple[CuratedPage, ...]:
    """Return the rendered Evidence section index and curated children."""
    index = CuratedPage(
        policy.evidence_label,
        policy.evidence_index_page,
    )
    return (index, *policy.curated_evidence_pages)


def require_mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    """Return a required mapping field."""
    result = value.get(key)
    if not isinstance(result, dict):
        raise NavigationError(f"Navigation policy mapping is missing: {key}")
    return result


def require_string(value: Mapping[str, Any], key: str) -> str:
    """Return a required non-empty string field."""
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise NavigationError(f"Navigation policy string is missing: {key}")
    return result.strip()


def require_strings(value: Mapping[str, Any], key: str) -> tuple[str, ...]:
    """Return a required string array without duplicates."""
    result = value.get(key)
    if not isinstance(result, list):
        raise NavigationError(f"Navigation policy array is missing: {key}")
    strings = tuple(dict.fromkeys(str(item).strip() for item in result))
    if not strings or any(not item for item in strings):
        raise NavigationError(f"Navigation policy array is invalid: {key}")
    return strings


def require_curated_pages(value: Any) -> tuple[CuratedPage, ...]:
    """Return validated curated evidence page entries."""
    if not isinstance(value, list) or not value:
        raise NavigationError("Curated evidence pages are missing")
    pages: list[CuratedPage] = []
    for item in value:
        if not isinstance(item, dict):
            raise NavigationError("Curated evidence page must be an object")
        pages.append(
            CuratedPage(
                require_string(item, "label"),
                require_string(item, "path"),
            )
        )
    paths = [item.path for item in pages]
    if len(paths) != len(set(paths)):
        raise NavigationError("Curated evidence pages contain duplicates")
    return tuple(pages)


def humanize(value: str) -> str:
    """Convert a source name into a stable navigation label."""
    stem = Path(value).stem
    match = _NUMBER_PREFIX.match(stem)
    if match:
        stem = match.group(2) or match.group(1)
    return re.sub(r"[-_]+", " ", stem).strip() or value


def document_label(path: Path, policy: NavigationPolicy) -> str:
    """Return policy-selected navigation label for one Markdown document."""
    document = MarkdownDocument.load(path)
    value = document.scalar(policy.label_front_matter_key)
    label = value or document.first_h1() or humanize(path.name)
    normalized = " ".join(label.split())
    if len(normalized) > policy.maximum_label_length:
        raise NavigationError(
            f"Navigation label exceeds {policy.maximum_label_length}: "
            f"{path}: {normalized}"
        )
    return normalized


def sort_key(path: Path) -> tuple[int, int, str]:
    """Sort numeric Daux prefixes before alphabetical source names."""
    match = _NUMBER_PREFIX.match(path.stem)
    if match:
        return (0, int(match.group(1)), path.name.casefold())
    return (1, 999999, path.name.casefold())


def relative_path(path: Path, source: Path) -> str:
    """Return one POSIX path relative to staged source."""
    return path.relative_to(source).as_posix()


@dataclass
class NavigationBuilder:
    """Build policy-driven MkDocs navigation from staged Markdown."""

    source: Path
    policy: NavigationPolicy
    excluded: set[str]

    @classmethod
    def create(cls, source: Path, policy: NavigationPolicy) -> "NavigationBuilder":
        """Create a builder and derive cataloged record exclusions."""
        root = source.expanduser().resolve()
        catalog_path = require_inside(root, Path(policy.evidence_catalog_path))
        catalog = EvidenceCatalog.load(catalog_path)
        excluded = catalog.staged_paths(policy.evidence_source_prefix)
        return cls(root, policy, excluded)

    def directory_entries(self, directory: Path) -> list[Any]:
        """Build recursive entries for one staged directory."""
        entries: list[Any] = []
        index = directory / "index.md"
        if index.is_file() and relative_path(index, self.source) not in self.excluded:
            entries.append({"Overview": relative_path(index, self.source)})
        for child in sorted(directory.iterdir(), key=sort_key):
            if child.name == "index.md" or child.name.startswith("."):
                continue
            if child.is_dir():
                nested = self.directory_entries(child)
                if nested:
                    entries.append({humanize(child.name): nested})
            elif child.suffix.lower() == ".md":
                relative = relative_path(child, self.source)
                if relative not in self.excluded:
                    entries.append({document_label(child, self.policy): relative})
        return entries

    def evidence_entry(self) -> dict[str, list[Any]]:
        """Return a section index followed by curated Evidence children."""
        index = self.source / self.policy.evidence_index_page
        if not index.is_file():
            raise NavigationError(
                f"Evidence index page is missing: "
                f"{self.policy.evidence_index_page}"
            )
        entries: list[Any] = [self.policy.evidence_index_page]
        for item in self.policy.curated_evidence_pages:
            if not (self.source / item.path).is_file():
                raise NavigationError(f"Evidence page is missing: {item.path}")
            entries.append({item.label: item.path})
        return {self.policy.evidence_label: entries}

    def build(self) -> list[Any]:
        """Build the complete primary navigation tree."""
        landing = self.source / self.policy.landing_page
        if not landing.is_file():
            raise NavigationError(f"Landing page is missing: {landing}")
        nav: list[Any] = [{self.policy.root_label: self.policy.landing_page}]
        excluded_names = set(self.policy.excluded_top_level_names)
        for child in sorted(self.source.iterdir(), key=sort_key):
            if child.name in excluded_names:
                continue
            if child.name == self.policy.evidence_root:
                nav.append(self.evidence_entry())
            elif child.is_dir():
                entries = self.directory_entries(child)
                if entries:
                    nav.append({humanize(child.name): entries})
            elif child.suffix.lower() == ".md":
                relative = relative_path(child, self.source)
                if relative not in self.excluded:
                    nav.append({document_label(child, self.policy): relative})
        return nav

    def hidden_paths(self) -> list[str]:
        """Return Markdown paths intentionally hidden from primary navigation."""
        hidden = set(self.excluded)
        for group in self.policy.hidden_evidence_groups:
            root = self.source / self.policy.evidence_root / group
            if not root.is_dir():
                continue
            for path in root.glob("*.md"):
                if path.name != "index.md":
                    hidden.add(relative_path(path, self.source))
        return sorted(hidden)


def nav_leaf_paths(value: Any) -> list[str]:
    """Return all leaf Markdown paths from a nested nav structure."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [path for item in value for path in nav_leaf_paths(item)]
    if isinstance(value, dict):
        return [path for item in value.values() for path in nav_leaf_paths(item)]
    raise NavigationError(f"Unexpected nav value: {type(value).__name__}")


class MaterialLinkParser(HTMLParser):
    """Collect links while distinguishing Material primary and secondary nav."""

    def __init__(self, policy: NavigationPolicy, *, primary_only: bool = False) -> None:
        """Initialize parser state from the navigation policy."""
        super().__init__(convert_charrefs=True)
        self.policy = policy
        self.primary_only = primary_only
        self.nav_stack: list[str] = []
        self.href: str | None = None
        self.text: list[str] = []
        self.links: list[dict[str, str]] = []

    def nav_kind(self, classes: set[str]) -> str:
        """Classify one Material navigation element."""
        if self.policy.material_primary_classes.issubset(classes):
            return "primary"
        if self.policy.material_secondary_classes.issubset(classes):
            return "secondary"
        return "other"

    def primary_link(self, classes: set[str]) -> bool:
        """Return whether an anchor is a primary navigation leaf link."""
        return (
            "primary" in self.nav_stack
            and "secondary" not in self.nav_stack
            and self.policy.material_leaf_class in classes
        )

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        """Track navigation nesting and begin eligible anchors."""
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "nav":
            self.nav_stack.append(self.nav_kind(classes))
        eligible = not self.primary_only or self.primary_link(classes)
        if tag == "a" and self.href is None and eligible:
            href = attributes.get("href")
            if href is not None:
                self.href = href
                self.text = []

    def handle_endtag(self, tag: str) -> None:
        """Finalize anchors and leave nested navigation elements."""
        if tag == "a" and self.href is not None:
            label = " ".join(" ".join(self.text).split())
            self.links.append({"href": self.href, "label": label})
            self.href = None
            self.text = []
        if tag == "nav" and self.nav_stack:
            self.nav_stack.pop()

    def handle_data(self, data: str) -> None:
        """Collect visible anchor text."""
        if self.href is not None:
            value = " ".join(data.split())
            if value:
                self.text.append(value)


def parse_links(
    path: Path,
    policy: NavigationPolicy,
    *,
    primary_only: bool = False,
) -> list[dict[str, str]]:
    """Parse links from one generated HTML document."""
    if not path.is_file():
        raise NavigationError(f"Generated HTML is missing: {path}")
    parser = MaterialLinkParser(policy, primary_only=primary_only)
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.links


def source_relative_path(
    source_path: str,
    prefix: str = "markdown/",
) -> PurePosixPath:
    """Normalize repository-prefixed or staged-relative Markdown paths."""
    value = source_path.strip()
    if not value:
        raise NavigationError("Evidence source path is empty")
    if "\\" in value:
        raise NavigationError(f"Evidence source path uses backslashes: {value}")
    if value.startswith(prefix):
        value = value[len(prefix) :]
    relative = PurePosixPath(value)
    invalid = (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
        or relative.suffix.lower() != ".md"
    )
    if invalid:
        raise NavigationError(f"Unexpected source path: {source_path}")
    return relative


def source_url(source_path: str, prefix: str = "markdown/") -> str:
    """Map repository or staged Markdown source paths to a directory URL."""
    relative = source_relative_path(source_path, prefix)
    target = (
        relative.parent
        if relative.name == "index.md"
        else relative.with_suffix("")
    )
    value = target.as_posix().rstrip("/")
    return value + ("/" if value else "")


def normalized_primary_hrefs(links: Sequence[Mapping[str, str]]) -> list[str]:
    """Normalize primary navigation hrefs relative to site root."""
    result: list[str] = []
    for link in links:
        path = urlparse(link["href"]).path
        while path.startswith("../"):
            path = path[3:]
        path = path.removeprefix("./").removeprefix("/")
        result.append(path.rstrip("/") + ("/" if path else ""))
    return result


def evidence_index_pages(site: Path, policy: NavigationPolicy) -> list[Path]:
    """Return generated evidence index pages that may link to records."""
    root = site / policy.evidence_root
    if not root.is_dir():
        raise NavigationError(f"Evidence site directory is missing: {root}")
    return sorted(path for path in root.rglob("index.html") if path.is_file())


def linked_site_urls(
    site: Path,
    pages: Iterable[Path],
    policy: NavigationPolicy,
) -> set[str]:
    """Resolve generated index links to site-relative URLs."""
    result: set[str] = set()
    for page in pages:
        base = "/" + page.relative_to(site).as_posix()
        for link in parse_links(page, policy):
            href = link["href"]
            if urlparse(href).scheme or href.startswith("#"):
                continue
            resolved = urlparse(urljoin(base, href)).path.removeprefix("/")
            if resolved.endswith("index.html"):
                resolved = resolved[:-10]
            result.add(resolved.rstrip("/") + ("/" if resolved else ""))
    return result
