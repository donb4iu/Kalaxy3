#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, tempfile, sys
from pathlib import Path
SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))
from legacy_evidence_projection import LegacyEvidenceError, build_projection, write_projection

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "sage-legacy-evidence-sources.json"
EXPECTED_DIGESTS = {
    "kalaxy2-cloudflare-service": "9973bd1d067dd0dc92a4cb813a1fe41736389046cbe6d247e7349b26f0105d71",
    "kalaxy2-cloudflare-ssh-access": "27c95a22a097a15d6e7a847ba9e5b725f3629d1b1346775a4d4cc8ccb2b05d2c",
}

def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)

def expect_error(fn, message: str) -> None:
    try:
        fn()
    except LegacyEvidenceError:
        return
    raise RuntimeError(message)

def descriptor(entry, source_bytes):
    return {
        "repository": entry["repository"],
        "repository_url": entry["repository_url"],
        "path": entry["path"],
        "commit": entry["commit"],
        "historical_time_context": entry["historical_time_context"],
        "expected_content_sha256": hashlib.sha256(source_bytes).hexdigest(),
    }

def project(entry, payload, claims, projection_id):
    before = hashlib.sha256(payload).hexdigest()
    record = build_projection(
        projection_id=projection_id,
        source_descriptor=descriptor(entry, payload),
        source_bytes=payload,
        claims=claims,
        projected_by={"participant_class":"llm","identity":"guardrail-fixture"},
    )
    require(hashlib.sha256(payload).hexdigest() == before, "historical source fixture changed during projection")
    return record

def main() -> int:
    registry = json.loads(REGISTRY.read_text())
    sources = {item["source_id"]: item for item in registry["sources"]}
    require(set(sources) == set(EXPECTED_DIGESTS), "pinned Kalaxy2 Cloudflare source registry changed")
    for source_id, entry in sources.items():
        require(entry["current_authority"] is False, "legacy source became current authority")
        require(entry["projection_required"] is True, "legacy source bypassed projection")
        require(entry["current_revalidation_required"] is True, "legacy source bypassed current revalidation")
        require(entry["captured_content_sha256"] == EXPECTED_DIGESTS[source_id], "pinned legacy capture digest changed")
        require(entry["publication"]["surface_in_public_evidence"] is True, "legacy source lost public evidence lineage")

    service_payload = b"Historical Kalaxy2 fixture: cloudflared version 2024.4.1; systemd cloudflared tunnel service installed and enabled.\n"
    service = project(sources["kalaxy2-cloudflare-service"], service_payload, [
        {"claim_id":"service-version","statement":"Kalaxy2 recorded cloudflared 2024.4.1.","classification":"directly-supported","source_basis":["fixture records cloudflared 2024.4.1"],"rationale":"Direct historical observation."},
        {"claim_id":"service-local-experience","statement":"Kalaxy2 had prior local operational experience with a cloudflared systemd service.","classification":"safely-derivable","source_basis":["fixture records installed and enabled systemd service"],"rationale":"The conclusion is bounded to historical local operation."},
        {"claim_id":"service-current-security","statement":"Current Kalaxy3 security adequacy is not established by this history.","classification":"requires-current-revalidation","source_basis":[],"rationale":"Current security posture requires current evidence."},
    ], "fixture-kalaxy2-cloudflare-service")

    ssh_payload = b"Historical Kalaxy2 fixture: proxyCommand cloudflared access ssh --hostname %h; successful SSH session recorded.\n"
    ssh = project(sources["kalaxy2-cloudflare-ssh-access"], ssh_payload, [
        {"claim_id":"ssh-proxy-command","statement":"Kalaxy2 recorded SSH client use of cloudflared access ssh --hostname %h.","classification":"directly-supported","source_basis":["fixture records cloudflared access ssh --hostname %h"],"rationale":"Direct historical configuration observation."},
        {"claim_id":"ssh-current-fit","statement":"Current Kalaxy3 SSH fit is unknown until current architecture and product guidance are assessed.","classification":"unknown","source_basis":[],"rationale":"The historical source cannot establish current fit."},
        {"claim_id":"ssh-architect-boundary","statement":"Any present privileged remote-management exposure requires Architect disposition.","classification":"requires-Architect-disposition","source_basis":[],"rationale":"The current trust-boundary decision is human-authoritative."},
    ], "fixture-kalaxy2-cloudflare-ssh")

    for record in (service, ssh):
        authority = record["authority"]
        for field in (
            "projection_is_current_authority",
            "projection_may_upgrade_confidence",
            "projection_may_establish_current_applicability",
            "projection_may_claim_current_success",
            "projection_may_claim_current_security_posture",
            "projection_may_claim_current_validation",
        ):
            require(authority[field] is False, f"projection silently upgraded {field}")
        require(record["publication"]["legacy_label_required"] is True, "legacy publication label missing")

    bad_commit = descriptor(sources["kalaxy2-cloudflare-service"], service_payload)
    bad_commit["commit"] = "deadbeef"
    expect_error(lambda: build_projection(projection_id="bad-commit", source_descriptor=bad_commit, source_bytes=service_payload, claims=service["projection"]["claims"], projected_by={"participant_class":"llm","identity":"guardrail"}), "invalid commit provenance did not fail closed")

    bad_digest = descriptor(sources["kalaxy2-cloudflare-service"], service_payload)
    bad_digest["expected_content_sha256"] = "0" * 64
    expect_error(lambda: build_projection(projection_id="bad-digest", source_descriptor=bad_digest, source_bytes=service_payload, claims=service["projection"]["claims"], projected_by={"participant_class":"llm","identity":"guardrail"}), "content provenance mismatch did not fail closed")

    bad_class = copy.deepcopy(service["projection"]["claims"])
    bad_class[0]["classification"] = "current-authority"
    expect_error(lambda: build_projection(projection_id="bad-class", source_descriptor=descriptor(sources["kalaxy2-cloudflare-service"], service_payload), source_bytes=service_payload, claims=bad_class, projected_by={"participant_class":"llm","identity":"guardrail"}), "semantic authority upgrade classification did not fail closed")

    missing_basis = copy.deepcopy(service["projection"]["claims"])
    missing_basis[0]["source_basis"] = []
    expect_error(lambda: build_projection(projection_id="missing-basis", source_descriptor=descriptor(sources["kalaxy2-cloudflare-service"], service_payload), source_bytes=service_payload, claims=missing_basis, projected_by={"participant_class":"llm","identity":"guardrail"}), "unsupported direct claim did not fail closed")

    with tempfile.TemporaryDirectory(prefix="sage-legacy-projection-") as td:
        output = Path(td) / "projection.json"
        write_projection(output, service)
        preserved = output.read_bytes()
        expect_error(lambda: write_projection(output, ssh), "projection output rewrite did not fail closed")
        require(output.read_bytes() == preserved, "failed rewrite changed existing projection output")

    print("PASS both pinned Kalaxy2 Cloudflare source anchors and capture digests")
    print("PASS supported, derived, unknown, revalidation, and Architect-disposition classifications")
    print("PASS invalid commit and content-digest provenance fail closed")
    print("PASS silent authority/applicability/confidence/success/security/validation upgrades prohibited")
    print("PASS existing projection output and historical fixture bytes are not rewritten")
    print("Kalaxy3 SAGE legacy evidence projection guardrail: PASS")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, RuntimeError, LegacyEvidenceError, ValueError, TypeError, KeyError) as error:
        print("Kalaxy3 SAGE legacy evidence projection guardrail: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
