"""Independent-source omission challenge over an exact committed Git tree.

The probe set is an explicitly attributable input, not independent ground truth.
No returned path is automatically semantically relevant or authoritative.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Sequence

from sage_context_discovery import inventory, sensitive_path

MAX_PROBES = 12
MAX_CHALLENGES = 120


def validate_probes(probes: Sequence[str]) -> list[str]:
    """Normalize bounded nontrivial literal discovery probes.

    Args:
        probes: Independently specified or explicitly attributed probe phrases.
    """
    if not isinstance(probes, list) or len(probes) > MAX_PROBES:
        raise ValueError("Expected at most 12 probe phrases")
    normalized: set[str] = set()
    for probe in probes:
        if (not isinstance(probe, str)
                or not re.fullmatch(r"[A-Za-z0-9 _-]{4,64}", probe)):
            raise ValueError("Invalid bounded probe")
        normalized.add(probe.lower().strip())
    return sorted(normalized)


def probe_hits(repo: Path, revision: str, probes: Sequence[str]) -> set[str]:
    """Search all committed textual paths, not the selected candidate list.

    Args:
        repo: Existing repository with required objects.
        revision: Exact commit identifier.
        probes: Validated literal alternatives/obligation cues.
    """
    if not probes:
        return set()
    args = ["git", "-C", str(repo), "grep", "-I", "-i", "-l", "-F"]
    for probe in probes:
        args.extend(["-e", probe])
    proc = subprocess.run([*args, revision, "--"], capture_output=True)
    if proc.returncode not in (0, 1):
        raise RuntimeError("Pinned omission probe failed")
    prefix = (revision + ":").encode("ascii")
    return {line[len(prefix):].decode("utf-8", errors="strict")
            for line in proc.stdout.splitlines() if line.startswith(prefix)}


def challenge(repo: Path, revision: str, nominated: set[str],
              probes: Sequence[str], labeled_paths: set[str]
              ) -> dict[str, Any]:
    """Expose independently found sources outside current nomination.

    Args:
        repo: Existing Git checkout.
        revision: Pinned source commit.
        nominated: Paths from candidate retrieval lanes.
        probes: Critic search cues, not semantic labels.
        labeled_paths: External reviewer-labelled paths, regardless of selection.
    """
    universe = inventory(repo, revision)
    matches = probe_hits(repo, revision, probes) | labeled_paths
    unexpected = sorted((matches & universe.keys()) - nominated)
    visible = [path for path in unexpected if not sensitive_path(path)]
    excluded = sorted(set(unexpected) - set(visible))
    return {
        "schema": "sage-context-omission-challenge-v1",
        "feature_revision": revision,
        "method": "pinned_git_full_tree_literal_probe_and_external_labels",
        "probe_digest": hashlib.sha256("\n".join(probes).encode()).hexdigest(),
        "probe_terms": list(probes),
        "probe_hit_count": len(matches & universe.keys()),
        "nominated_count": len(nominated),
        "outside_nomination_total": len(unexpected),
        "outside_nomination_visible_paths": visible[:MAX_CHALLENGES],
        "outside_nomination_truncated": len(visible) > MAX_CHALLENGES,
        "restricted_outside_count": len(excluded),
        "label_paths_not_in_git": sorted(labeled_paths - universe.keys()),
        "semantically_validated": False,
        "omission_completeness_verified": False,
    }
