#!/usr/bin/env python3
"""Guard persistent-LLM results against Architect-objective semantic drift."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
STANDARD = (
    ROOT
    / "markdown/standards/"
    / "kalaxy3-sage-persistent-llm-objective-context-process.md"
)
SAGE = ROOT / "SAGE.md"
MAKEFILE = ROOT / "Makefile"

REQUIRED_MARKERS = (
    "founding Architect-expressed objective",
    "alignment audit",
    "MUST remain understandable and useful if",
    "MUST NOT substitute",
    "persistent-LLM alignment defect",
)

INTERNAL_ONLY_TERMS = (
    "guardrail",
    "receipt",
    "semantic confirmation",
    "planning source",
    "intent-to-outcome",
    "candidate persistence",
    "lifecycle boundary",
    "fresh role",
    "sha256",
    "state transition",
)


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest for one UTF-8 string."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_result(path: Path) -> Mapping[str, Any]:
    """Load one persistent-LLM audit projection from JSON."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("persistent-LLM result projection must be an object")
    return value


def validate_repository_contract() -> list[str]:
    """Validate repository publication and aggregate-guardrail wiring."""
    failures: list[str] = []
    for path in (STANDARD, SAGE, MAKEFILE):
        if not path.is_file():
            failures.append(f"missing required contract file: {path}")
    if failures:
        return failures

    standard = " ".join(
        STANDARD.read_text(encoding="utf-8").split()
    )
    sage = " ".join(SAGE.read_text(encoding="utf-8").split())
    makefile = MAKEFILE.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        normalized_marker = " ".join(marker.split())
        if normalized_marker not in standard or normalized_marker not in sage:
            failures.append(
                f"missing objective-context marker: {marker}"
            )
    for target in (
        "sage-persistent-llm-objective-context-self-test",
        "sage-persistent-llm-objective-context-guardrail",
    ):
        if target not in makefile:
            failures.append(f"Makefile missing {target}")
    return failures


def validate_context(
    result: Mapping[str, Any],
    founding_request: str | None = None,
) -> list[str]:
    """Validate one Architect-objective context projection."""
    failures: list[str] = []
    required = (
        "founding_architect_objective",
        "founding_request_sha256",
        "progress",
        "why",
        "effect",
        "remaining",
        "sage_trace",
    )
    for key in required:
        if key not in result:
            failures.append(f"missing result field: {key}")
    if failures:
        return failures

    objective = str(result["founding_architect_objective"]).strip()
    fields = [str(result[key]).strip() for key in ("progress", "why", "effect")]
    if not objective or any(len(value) < 20 for value in fields):
        failures.append("Architect-objective explanation is materially incomplete")

    if founding_request is not None:
        expected = sha256_text(founding_request.strip())
        if result["founding_request_sha256"] != expected:
            failures.append("founding Architect request digest does not match")

    combined = " ".join(fields)
    if len(combined) > 1600:
        failures.append("Architect-objective explanation is not succinct")

    objective_is_sage = "sage" in objective.casefold()
    if not objective_is_sage:
        lowered = combined.casefold()
        hits = [term for term in INTERNAL_ONLY_TERMS if term in lowered]
        if len(hits) >= 2:
            failures.append(
                "Architect-objective explanation is framed primarily in "
                "SAGE-internal vocabulary"
            )
    return failures


def run_self_test() -> list[str]:
    """Exercise positive and negative objective-context audit fixtures."""
    failures: list[str] = []
    request = "Enable secure remote development without weakening local access."
    good = {
        "founding_architect_objective": request,
        "founding_request_sha256": sha256_text(request),
        "progress": (
            "Remote-development implementation can now proceed through the "
            "normal automated engineering path."
        ),
        "why": (
            "The prior response format was unreliable and prevented safe "
            "automation of the approved remote-access work."
        ),
        "effect": (
            "The approved security design remains unchanged while the "
            "implementation path is now machine-consumable."
        ),
        "remaining": "Remote routing and device-trust acceptance still require proof.",
        "sage_trace": {"status": "supporting-evidence"},
    }
    failures.extend(f"good fixture: {item}" for item in validate_context(good, request))

    bad = dict(good)
    bad["progress"] = "Guardrail passed and receipt advanced lifecycle boundary."
    bad["why"] = "Semantic confirmation produced the planning source and SHA256."
    bad["effect"] = "Candidate persistence moved the fresh role state transition."
    if not validate_context(bad, request):
        failures.append("internal-only negative fixture was accepted")

    wrong = dict(good)
    wrong["founding_request_sha256"] = "0" * 64
    if not validate_context(wrong, request):
        failures.append("wrong founding-request binding was accepted")
    return failures


def main() -> int:
    """Run repository guardrail, self-test, or one result audit."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--result", type=Path)
    parser.add_argument("--founding-request", type=Path)
    args = parser.parse_args()

    failures = validate_repository_contract()
    if args.self_test:
        failures.extend(run_self_test())
    if args.result:
        request = None
        if args.founding_request:
            request = args.founding_request.read_text(encoding="utf-8")
        failures.extend(validate_context(load_result(args.result), request))

    if failures:
        print("Kalaxy3 SAGE persistent LLM objective-context guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("Kalaxy3 SAGE persistent LLM objective-context guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
