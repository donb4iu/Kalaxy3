\
#!/usr/bin/env python3
"""Prepare and validate canonical Kalaxy3 SAGE evidence generation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any, Final, Sequence


ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-evidence-policy.json"
SECRET_PATTERNS: Final = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\bauthorization:\s*bearer\s+\S+"),
    re.compile(
        r"(?i)\b(api[_-]?key|access[_-]?token|password)"
        r"\s*[:=]\s*(?!\$\{\{\s*secrets\.)[^\s<>{}]+"
    ),
)


def sha256_bytes(content: bytes) -> str:
    """Return a SHA-256 hexadecimal digest."""
    return hashlib.sha256(content).hexdigest()


def sha256_path(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    """Load one JSON object from disk."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def load_preflight_module() -> ModuleType:
    """Load the repository SAGE discovery implementation."""
    path = ROOT / "scripts/sage/sage-change-preflight.py"
    spec = importlib.util.spec_from_file_location(
        "sage_change_preflight",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load SAGE change preflight")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_policy() -> dict[str, Any]:
    """Load the repository evidence-orchestration policy."""
    return load_json(POLICY_PATH)


def required_policy_fields() -> set[str]:
    """Return required top-level policy fields."""
    return {
        "schema_version",
        "canonical_request_path",
        "canonical_request_sha256",
        "standard_path",
        "metadata_contract_path",
        "record_template_path",
        "manifest_template_path",
        "publication_process_path",
        "orchestration_process_path",
        "publisher_path",
        "indexer_path",
        "discovery_map_path",
        "minimum_quality_requirements",
        "plain_language_examples",
        "required_bundle_files",
        "default_output",
    }


def validate_policy(policy: dict[str, Any]) -> list[str]:
    """Validate the evidence-orchestration policy."""
    failures: list[str] = []
    missing = sorted(required_policy_fields() - set(policy))
    if missing:
        failures.append(f"Policy fields missing: {missing}")

    if policy.get("schema_version") != "1.0":
        failures.append("Policy schema_version must be 1.0")

    requirements = policy.get("minimum_quality_requirements")
    if not isinstance(requirements, list) or len(requirements) < 15:
        failures.append(
            "minimum_quality_requirements must contain at least 15 items"
        )

    examples = policy.get("plain_language_examples")
    if not isinstance(examples, list) or len(examples) < 4:
        failures.append(
            "plain_language_examples must contain at least four items"
        )

    required_files = policy.get("required_bundle_files")
    if not isinstance(required_files, list) or not required_files:
        failures.append("required_bundle_files must be non-empty")
    return failures


def canonical_request(policy: dict[str, Any]) -> str:
    """Return and verify the canonical evidence-generation request."""
    path = ROOT / str(policy["canonical_request_path"])
    content = path.read_text(encoding="utf-8")
    actual = sha256_bytes(content.encode("utf-8"))
    expected = str(policy["canonical_request_sha256"])
    if actual != expected:
        raise RuntimeError(
            "Canonical evidence request checksum mismatch"
        )
    return content


def run_git(*arguments: str) -> str:
    """Run Git in the repository and return standard output."""
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip()


def changed_paths(module: ModuleType) -> list[str]:
    """Return tracked, staged, and untracked changed paths."""
    return list(module.changed_paths())


def infer_contexts(
    module: ModuleType,
    request: str,
) -> list[dict[str, Any]]:
    """Infer and expand SAGE contexts for the request."""
    authority_map = module.load_authority_map(
        ROOT / "sage-change-authority.json"
    )
    failures = module.validate_authority_map(authority_map)
    if failures:
        raise RuntimeError("; ".join(failures))

    initial = module.infer_context_ids(
        authority_map,
        request,
        changed_paths(module),
    )
    selected = module.expand_dependencies(
        authority_map,
        initial,
    )
    return list(module.ordered_contexts(authority_map, selected))


def repository_snapshot(module: ModuleType) -> dict[str, Any]:
    """Collect non-destructive repository evidence."""
    return {
        "repository_root": str(ROOT),
        "branch": run_git("branch", "--show-current"),
        "head": run_git("rev-parse", "HEAD"),
        "head_subject": run_git("log", "-1", "--format=%s"),
        "status_short": run_git("status", "--short"),
        "changed_paths": changed_paths(module),
        "diff_stat": run_git("diff", "--stat"),
        "diff": run_git("diff", "--no-ext-diff", "--"),
        "cached_diff_stat": run_git("diff", "--cached", "--stat"),
        "cached_diff": run_git(
            "diff",
            "--cached",
            "--no-ext-diff",
            "--",
        ),
        "recent_commits": run_git(
            "log",
            "-5",
            "--oneline",
            "--decorate",
        ),
    }


def secret_findings(text: str) -> list[str]:
    """Return labels for potential secrets found in text."""
    findings: list[str] = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(pattern.pattern)
    return findings


def require_safe_text(label: str, text: str) -> None:
    """Fail closed when text contains potential secrets."""
    if secret_findings(text):
        raise RuntimeError(
            f"{label} contains potential secret material"
        )


def authority_paths(
    policy: dict[str, Any],
    contexts: Sequence[dict[str, Any]],
) -> list[str]:
    """Return all authority paths needed by the generator."""
    values = [
        str(policy["canonical_request_path"]),
        str(policy["standard_path"]),
        str(policy["metadata_contract_path"]),
        str(policy["record_template_path"]),
        str(policy["manifest_template_path"]),
        str(policy["publication_process_path"]),
        str(policy["orchestration_process_path"]),
        str(policy["publisher_path"]),
        str(policy["indexer_path"]),
        str(policy["discovery_map_path"]),
        "sage-evidence-policy.json",
    ]
    for context in contexts:
        values.extend(context["authoritative_files"])
    return list(dict.fromkeys(values))


def authority_inventory(
    paths: Sequence[str],
) -> list[dict[str, str]]:
    """Build a checksum inventory for authority files."""
    inventory: list[dict[str, str]] = []
    for relative in paths:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(
                f"Authority file does not exist: {relative}"
            )
        inventory.append(
            {
                "path": relative,
                "sha256": sha256_path(path),
            }
        )
    return inventory


def terminal_evidence_paths(
    explicit: Sequence[Path],
) -> list[Path]:
    """Combine CLI and environment terminal-evidence paths."""
    values = [path.resolve() for path in explicit]
    environment = os.environ.get(
        "SAGE_TERMINAL_EVIDENCE",
        "",
    )
    if environment:
        values.extend(
            Path(item).expanduser().resolve()
            for item in environment.split(os.pathsep)
            if item
        )
    return list(dict.fromkeys(values))


def read_terminal_evidence(
    paths: Sequence[Path],
) -> list[dict[str, str]]:
    """Read and validate supplied terminal evidence."""
    items: list[dict[str, str]] = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(
                f"Terminal evidence file not found: {path}"
            )
        text = path.read_text(encoding="utf-8")
        require_safe_text(str(path), text)
        items.append(
            {
                "name": path.name,
                "source_path": str(path),
                "sha256": sha256_bytes(
                    text.encode("utf-8")
                ),
                "content": text,
            }
        )
    return items


def context_lines(
    contexts: Sequence[dict[str, Any]],
    field: str,
) -> list[str]:
    """Flatten and de-duplicate one context field."""
    values: list[str] = []
    for context in contexts:
        values.extend(str(item) for item in context[field])
    return list(dict.fromkeys(values))


def render_brief(
    request: str,
    canonical: str,
    policy: dict[str, Any],
    contexts: Sequence[dict[str, Any]],
    snapshot: dict[str, Any],
    terminal_count: int,
) -> str:
    """Render the canonical evidence-generation brief."""
    context_ids = [str(item["id"]) for item in contexts]
    authority = context_lines(
        contexts,
        "authoritative_files",
    )
    baseline = context_lines(contexts, "baseline_checks")
    validation = context_lines(
        contexts,
        "required_validation",
    )

    lines = [
        "# Kalaxy3 SAGE evidence-generation brief",
        "",
        "## Original requester language",
        "",
        "```text",
        request,
        "```",
        "",
        "The original request is authoritative context and must not "
        "be rewritten into a weaker requirement.",
        "",
        "## Automatically applied canonical request",
        "",
        canonical.rstrip(),
        "",
        "## Inferred SAGE contexts",
        "",
    ]
    lines.extend(f"- `{value}`" for value in context_ids)
    lines.extend(
        [
            "",
            "## Discovered authoritative files",
            "",
        ]
    )
    lines.extend(f"- `{value}`" for value in authority)
    lines.extend(
        [
            "",
            "## Baseline checks discovered",
            "",
        ]
    )
    lines.extend(f"- `{value}`" for value in baseline)
    lines.extend(
        [
            "",
            "## Required validation discovered",
            "",
        ]
    )
    lines.extend(f"- `{value}`" for value in validation)
    lines.extend(
        [
            "",
            "## Minimum evidence quality contract",
            "",
        ]
    )
    lines.extend(
        f"{index}. {value}"
        for index, value in enumerate(
            policy["minimum_quality_requirements"],
            start=1,
        )
    )
    lines.extend(
        [
            "",
            "## Repository working-session boundary",
            "",
            f"- Branch: `{snapshot['branch']}`",
            f"- HEAD: `{snapshot['head']}`",
            (
                "- Changed path count: "
                f"{len(snapshot['changed_paths'])}"
            ),
            (
                "- Supplied terminal evidence files: "
                f"{terminal_count}"
            ),
            "",
            "## Generator output contract",
            "",
            "Generate one schema 1.2 SAGE evidence package ZIP.",
            "The package must pass:",
            "",
            "```bash",
            "python3 scripts/sage/sage-publish.py check "
            "~/Downloads/<package>.zip",
            "```",
            "",
            "Return only the package and these standard commands:",
            "",
            "```bash",
            "python3 scripts/sage/sage-publish.py check "
            "~/Downloads/<package>.zip",
            "python3 scripts/sage/sage-publish.py publish "
            "~/Downloads/<package>.zip --push",
            "```",
            "",
            "Do not invent a separate metadata, navigation, "
            "validation, Git, or publication workflow.",
            "",
            "## Explicit evidence gaps",
            "",
        ]
    )
    if terminal_count:
        lines.append(
            "- Supplied terminal evidence is included in this bundle."
        )
    else:
        lines.append(
            "- No external terminal transcript was supplied. "
            "Use repository evidence and mark uncaptured runtime "
            "observations as evidence gaps rather than inventing them."
        )
    lines.append("")
    return "\n".join(lines)


def render_repository_evidence(
    snapshot: dict[str, Any],
) -> str:
    """Render repository evidence as Markdown."""
    sections = [
        ("Git status", snapshot["status_short"]),
        ("Changed paths", "\n".join(snapshot["changed_paths"])),
        ("Unstaged diff stat", snapshot["diff_stat"]),
        ("Unstaged diff", snapshot["diff"]),
        ("Staged diff stat", snapshot["cached_diff_stat"]),
        ("Staged diff", snapshot["cached_diff"]),
        ("Recent commits", snapshot["recent_commits"]),
    ]
    lines = [
        "# Repository evidence",
        "",
        f"- Branch: `{snapshot['branch']}`",
        f"- HEAD: `{snapshot['head']}`",
        f"- HEAD subject: {snapshot['head_subject']}",
        "",
    ]
    for title, content in sections:
        lines.extend(
            [
                f"## {title}",
                "",
                "```text",
                content or "(none)",
                "```",
                "",
            ]
        )
    rendered = "\n".join(lines)
    require_safe_text("Repository evidence", rendered)
    return rendered


def copy_text_file(
    source: Path,
    destination: Path,
) -> None:
    """Copy one validated UTF-8 text file."""
    content = source.read_text(encoding="utf-8")
    require_safe_text(str(source), content)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def write_bundle_files(
    directory: Path,
    request: str,
    policy: dict[str, Any],
    contexts: Sequence[dict[str, Any]],
    snapshot: dict[str, Any],
    terminal: Sequence[dict[str, str]],
) -> None:
    """Write all evidence-generation input files."""
    canonical = canonical_request(policy)
    brief = render_brief(
        request,
        canonical,
        policy,
        contexts,
        snapshot,
        len(terminal),
    )
    repository_evidence = render_repository_evidence(snapshot)
    authority = authority_paths(policy, contexts)

    context = {
        "schema_version": "1.0",
        "original_request": request,
        "contexts": [
            {
                "id": item["id"],
                "working_directory": item["working_directory"],
                "authoritative_files": item["authoritative_files"],
                "baseline_checks": item["baseline_checks"],
                "required_validation": item[
                    "required_validation"
                ],
                "evidence_process": item["evidence_process"],
            }
            for item in contexts
        ],
        "repository": snapshot,
        "authority_inventory": authority_inventory(authority),
        "terminal_evidence": [
            {
                "name": item["name"],
                "source_path": item["source_path"],
                "sha256": item["sha256"],
            }
            for item in terminal
        ],
    }

    (directory / "sage-evidence-generation-brief.md").write_text(
        brief,
        encoding="utf-8",
    )
    (directory / "repository-evidence.md").write_text(
        repository_evidence,
        encoding="utf-8",
    )
    (directory / "sage-session-context.json").write_text(
        json.dumps(context, indent=4) + "\n",
        encoding="utf-8",
    )

    for relative in authority:
        copy_text_file(
            ROOT / relative,
            directory / "authorities" / relative,
        )

    for item in terminal:
        destination = (
            directory
            / "terminal-evidence"
            / item["name"]
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            item["content"],
            encoding="utf-8",
        )


def bundle_manifest(directory: Path) -> dict[str, Any]:
    """Build a complete checksum manifest for the bundle."""
    files = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != "bundle-manifest.json":
            files.append(
                {
                    "path": path.relative_to(directory).as_posix(),
                    "sha256": sha256_path(path),
                }
            )
    return {
        "schema_version": "1.0",
        "bundle_type": "sage-evidence-generation-inputs",
        "files": files,
    }


def create_zip(source: Path, output: Path) -> None:
    """Create a deterministic-path ZIP from the bundle directory."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(
                    path,
                    path.relative_to(source).as_posix(),
                )


def resolve_request(argument: str) -> str:
    """Resolve request text from CLI or environment."""
    request = argument or os.environ.get("SAGE_REQUEST", "")
    if not request:
        raise RuntimeError(
            "Provide --request or set SAGE_REQUEST"
        )
    return request


def resolve_output(
    argument: Path | None,
    policy: dict[str, Any],
) -> Path:
    """Resolve the evidence-input bundle output path."""
    raw = os.environ.get("SAGE_EVIDENCE_OUTPUT")
    output = argument or (
        Path(raw).expanduser()
        if raw
        else Path(str(policy["default_output"]))
    )
    output = output.resolve()
    try:
        output.relative_to(ROOT)
    except ValueError:
        return output
    raise RuntimeError(
        "Evidence input bundles must be written outside the repository"
    )


def capture(
    request: str,
    output: Path,
    terminal_paths: Sequence[Path],
) -> Path:
    """Create one canonical evidence-generation input bundle."""
    policy = load_policy()
    failures = validate_policy(policy)
    if failures:
        raise RuntimeError("; ".join(failures))

    module = load_preflight_module()
    contexts = infer_contexts(module, request)
    snapshot = repository_snapshot(module)
    terminal = read_terminal_evidence(terminal_paths)

    with tempfile.TemporaryDirectory(
        prefix="sage-evidence-inputs-"
    ) as temp_name:
        directory = Path(temp_name)
        write_bundle_files(
            directory,
            request,
            policy,
            contexts,
            snapshot,
            terminal,
        )
        manifest = bundle_manifest(directory)
        (directory / "bundle-manifest.json").write_text(
            json.dumps(manifest, indent=4) + "\n",
            encoding="utf-8",
        )
        create_zip(directory, output)
    return output


def check_package(package: Path) -> int:
    """Validate one generated SAGE package through the publisher."""
    result = subprocess.run(
        [
            "python3",
            "scripts/sage/sage-publish.py",
            "check",
            str(package.resolve()),
        ],
        cwd=ROOT,
        check=False,
    )
    return result.returncode


def self_test() -> list[str]:
    """Run evidence-orchestration regression tests."""
    failures: list[str] = []
    policy = load_policy()
    failures.extend(validate_policy(policy))

    try:
        canonical = canonical_request(policy)
    except RuntimeError as error:
        failures.append(str(error))
        canonical = ""

    module = load_preflight_module()
    for request in policy.get("plain_language_examples", []):
        contexts = infer_contexts(module, str(request))
        ids = {str(item["id"]) for item in contexts}
        if "evidence" not in ids:
            failures.append(
                "Plain-language request lacked evidence context: "
                f"{request!r}"
            )

    snapshot = repository_snapshot(module)
    contexts = infer_contexts(
        module,
        'Document "$HOME" literally.',
    )
    brief = render_brief(
        'Document "$HOME" literally.',
        canonical,
        policy,
        contexts,
        snapshot,
        0,
    )
    if 'Document "$HOME" literally.' not in brief:
        failures.append("Original request was not preserved literally")
    if canonical.rstrip() not in brief:
        failures.append("Canonical generation request was omitted")
    synthetic_secret = (
        "pass" + "word=" + "definitely-not-a-real-secret"
    )
    if not secret_findings(synthetic_secret):
        failures.append("Secret scanner negative test failed")

    github_secret_reference = (
        "pass" + "word: ${{ secrets.DOCKERHUB_TOKEN }}"
    )
    if secret_findings(github_secret_reference):
        failures.append(
            "GitHub Actions secret reference false-positive"
        )
    return failures


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and validate Kalaxy3 SAGE evidence generation"
        )
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    brief_parser = subparsers.add_parser(
        "brief",
        help="print the canonical evidence-generation brief",
    )
    brief_parser.add_argument("--request", default="")

    capture_parser = subparsers.add_parser(
        "capture",
        help="create a self-contained evidence-generation input ZIP",
    )
    capture_parser.add_argument("--request", default="")
    capture_parser.add_argument("--output", type=Path)
    capture_parser.add_argument(
        "--terminal-evidence",
        action="append",
        type=Path,
        default=[],
    )

    check_parser = subparsers.add_parser(
        "check",
        help="validate a generated SAGE evidence package",
    )
    check_parser.add_argument("--package", type=Path)

    subparsers.add_parser(
        "self-test",
        help="run orchestration regression tests",
    )
    return parser.parse_args()


def main() -> int:
    """Run the requested evidence-orchestration command."""
    args = parse_args()

    try:
        if args.command == "self-test":
            failures = self_test()
            if failures:
                print("Kalaxy3 SAGE evidence orchestration: FAIL")
                for failure in failures:
                    print(f"  - {failure}")
                return 1
            print(
                "Kalaxy3 SAGE evidence orchestration self-test: PASS"
            )
            return 0

        if args.command == "check":
            raw = args.package or (
                Path(os.environ["SAGE_PACKAGE"])
                if os.environ.get("SAGE_PACKAGE")
                else None
            )
            if raw is None:
                raise RuntimeError(
                    "Provide --package or set SAGE_PACKAGE"
                )
            return check_package(raw)

        request = resolve_request(args.request)
        policy = load_policy()
        module = load_preflight_module()
        contexts = infer_contexts(module, request)
        snapshot = repository_snapshot(module)
        terminal_paths = terminal_evidence_paths(
            getattr(args, "terminal_evidence", [])
        )

        if args.command == "brief":
            canonical = canonical_request(policy)
            print(
                render_brief(
                    request,
                    canonical,
                    policy,
                    contexts,
                    snapshot,
                    len(terminal_paths),
                )
            )
            return 0

        output = resolve_output(args.output, policy)
        created = capture(
            request,
            output,
            terminal_paths,
        )
        print(
            "Kalaxy3 SAGE evidence-generation inputs: PASS"
        )
        print(f"Bundle: {created}")
        print(
            "Next gate: generate one package from this bundle, then run"
        )
        print(
            "  SAGE_PACKAGE=<package.zip> make sage-evidence-check"
        )
        return 0
    except (
        KeyError,
        OSError,
        RuntimeError,
        subprocess.CalledProcessError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
    ) as error:
        print(
            "Kalaxy3 SAGE evidence orchestration: FAIL CLOSED"
        )
        print(f"  - {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
