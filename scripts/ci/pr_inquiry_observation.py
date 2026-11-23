#!/usr/bin/env python3
"""Publish an untrusted PR-work snapshot, with optional independently signed inquiry."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


class ObservationError(ValueError):
    """Represent a failed binding between a PR event and work evidence."""


def read_json(path: Path, limit: int = 262144) -> dict[str, Any]:
    """Read a bounded JSON object from a repository file.

    Args:
        path: File containing JSON object data.
        limit: Maximum accepted file size in bytes.
    """
    if not path.is_file() or path.stat().st_size > limit:
        raise ObservationError(f"Missing or oversized JSON file: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ObservationError("Expected a JSON object")
    return value


def load_projection_module(repo: Path) -> Any:
    """Load dashboard projection solely from the trusted base checkout.

    Args:
        repo: Trusted repository root containing projection source.
    """
    source = repo / "scripts/sage/architecture_helper/pr_work_projection.py"
    spec = importlib.util.spec_from_file_location("pr_work_projection", source)
    if spec is None or spec.loader is None:
        raise ObservationError("Trusted projection module is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event_info(event: Mapping[str, Any]) -> tuple[int, str, str]:
    """Extract the PR number, displayed title, and exact head commit.

    Args:
        event: GitHub-provided pull_request event payload.
    """
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        raise ObservationError("Not a pull_request event")
    number = pr.get("number")
    title = pr.get("title")
    head = pr.get("head", {})
    sha = head.get("sha") if isinstance(head, dict) else None
    if not isinstance(number, int) or number < 1:
        raise ObservationError("Invalid PR number")
    if not isinstance(title, str) or not title.strip():
        raise ObservationError("PR title missing")
    if not isinstance(sha, str) or len(sha) != 40:
        raise ObservationError("PR head SHA missing")
    if any(char not in "0123456789abcdef" for char in sha):
        raise ObservationError("PR head SHA malformed")
    return number, title[:250], sha


def verify_checkout(candidate: Path, sha: str) -> None:
    """Ensure data is from the exact PR revision in the GitHub event.

    Args:
        candidate: Untrusted PR head checkout.
        sha: Exact expected Git commit SHA.
    """
    process = subprocess.run(
        ["git", "-C", str(candidate), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False, timeout=10,
    )
    if process.returncode or process.stdout.strip() != sha:
        raise ObservationError("Candidate checkout does not match PR head")



def require_candidate_path(candidate: Path, path: Path) -> None:
    """Prevent untrusted PR symlinks from escaping its checkout.

    Args:
        candidate: Root of untrusted PR data.
        path: Evidence path constrained to that checkout.
    """
    if not path.resolve().is_relative_to(candidate.resolve()):
        raise ObservationError("PR evidence path escapes untrusted checkout")


def empty_thread(number: int, title: str) -> dict[str, Any]:
    """Create a clearly unverified dashboard shell when no record exists.

    Args:
        number: Pull request number.
        title: Untrusted PR title for presentation only.
    """
    return {
        "schema": "sage-pr-work-thread-v1",
        "objective": {"id": f"PR #{number}", "title": title,
                      "intent": "Objective intent not independently established"},
        "milestone": {"id": "not verified", "title": "No milestone record supplied",
                      "proposal": "No evidenced approach supplied"},
        "work": {"done": [], "doing": [], "next": [], "blocked": [
            "A PR-level work thread has not been supplied",
            "No independently attested semantic inquiry is available",
        ]},
        "inquiries": [], "iterations": [], "raci": [], "learnings": [], "concepts": [],
    }


def load_thread(candidate: Path, number: int, title: str,
                module: Any) -> tuple[dict[str, Any], str]:
    """Read candidate work-thread data without granting it any authority.

    Args:
        candidate: Checkout of untrusted pull-request data.
        number: Pull request number.
        title: Display title for a missing record.
        module: Trusted dashboard projection module.
    """
    path = candidate / f"docs/sage/pr-work/pr-{number}.json"
    require_candidate_path(candidate, path)
    if not path.exists():
        return module.validate_thread(empty_thread(number, title)), "missing"
    result = module.validate_thread(read_json(path))
    if result.get("pr_number") != number:
        raise ObservationError("PR work thread is not bound to its PR number")
    return result, "candidate_unverified"


def trusted_revision(trusted: Path) -> str | None:
    """Get an independently maintained semantic collection revision, if present.

    Args:
        trusted: Trusted base checkout, never candidate content.
    """
    path = trusted / ".github/sage/semantic-collection-revision.txt"
    if not path.is_file():
        return None
    revision = path.read_text(encoding="ascii").strip()
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ObservationError("Trusted semantic revision is malformed")
    return revision


def evaluate_inquiry(candidate: Path, trusted: Path, number: int,
                     thread: Mapping[str, Any], module: Any
                     ) -> tuple[dict[str, Any] | None, list[dict[str, Any]] | None, str]:
    """Verify receipt only with independently supplied trust anchors and revision.

    Args:
        candidate: Untrusted PR data, including optional signed receipt.
        trusted: Trusted base holding approved keys and collection revision.
        number: PR number used to constrain path resolution.
        thread: Claimed work thread, not authorizing evidence.
        module: Trusted dashboard module.
    """
    folder = candidate / f"docs/sage/pr-inquiry/pr-{number}"
    require_candidate_path(candidate, folder)
    if not folder.exists():
        return None, None, "missing"
    receipt, signature, proposal = (folder / name for name in (
        "receipt.json", "signature.bin", "proposal.md"))
    key = trusted / ".github/sage/authorized-signers/semantic-retrieval-controller.pem"
    revision = trusted_revision(trusted)
    for path in (receipt, signature, proposal):
        require_candidate_path(candidate, path)
    if not (receipt.is_file() and signature.is_file() and proposal.is_file()):
        return None, None, "incomplete"
    if not key.is_file() or revision is None:
        return None, None, "trusted_attester_not_configured"
    context = argparse.Namespace(receipt=receipt, signature=signature,
                                 trusted_key=key, proposal=proposal,
                                 collection_revision=revision)
    attestation, inquiries = module.load_verified_inquiry(context, thread)
    return attestation, inquiries, "attested_provenance_only"


def render(event_path: Path, candidate: Path, trusted: Path,
           output: Path, enforce: bool = False) -> dict[str, str]:
    """Build read-only dashboard and provenance status for one exact PR.

    Args:
        event_path: GitHub PR event object stored on the runner.
        candidate: Untrusted candidate checkout at event head SHA.
        trusted: Current trusted-base checkout.
        output: Destination for JSON and HTML projections.
        enforce: Reject missing or invalid attestation when explicitly enabled.
    """
    number, title, sha = event_info(read_json(event_path))
    verify_checkout(candidate, sha)
    module = load_projection_module(trusted)
    thread, thread_state = load_thread(candidate, number, title, module)
    try:
        attestation, inquiries, inquiry_state = evaluate_inquiry(
            candidate, trusted, number, thread, module)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        attestation, inquiries, inquiry_state = None, None, "invalid"
        print(f"::warning title=Semantic inquiry invalid::{type(error).__name__}")
    if inquiries is not None:
        thread = {**thread, "inquiries": inquiries}
    projected = module.project(thread, attestation)
    projected["source_pr_head"] = sha
    projected["source_pr_number"] = number
    projected["work_thread_status"] = thread_state
    projected["semantic_inquiry_status"] = inquiry_state
    output.mkdir(parents=True, exist_ok=True)
    (output / "work.json").write_text(json.dumps(projected, indent=2) + "\n")
    (output / "dashboard.html").write_text(module.html_page(projected))
    result = {"pr": str(number), "thread": thread_state, "inquiry": inquiry_state,
              "qualification": "not_granted"}
    (output / "status.json").write_text(json.dumps(result, indent=2) + "\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write("### SAGE PR work and semantic inquiry (advisory)\n")
            handle.write(f"- Work thread: `{thread_state}`\n")
            handle.write(f"- Semantic inquiry: `{inquiry_state}`\n")
            handle.write("- No approval or promotion authority granted\n")
    if enforce and inquiry_state != "attested_provenance_only":
        raise ObservationError(f"Required inquiry not attested: {inquiry_state}")
    return result


def main() -> None:
    """Run the existing advisory's additive work-status observation."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("event", "candidate", "trusted", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()
    try:
        result = render(args.event, args.candidate, args.trusted,
                        args.output, args.enforce)
    except (ObservationError, OSError, ValueError) as exc:
        print(f"ERROR={type(exc).__name__}:{exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"PR={result['pr']}; INQUIRY={result['inquiry']}; "
          f"WORK_THREAD={result['thread']}; PR_PROMOTION=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
