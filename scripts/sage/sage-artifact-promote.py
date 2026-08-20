#!/usr/bin/env python3
"""Prepare or execute exact-digest OCI artifact promotion."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import WorkflowError  # noqa: E402
from workflows.artifact_promotion import execute_promotion, prepare_promotion, validate_promotion_inputs  # noqa: E402


def _fixture_archive(path: Path) -> tuple[str, list[dict[str, str]], bytes]:
    child_payloads = []
    descriptors = []
    platforms = []
    for architecture, seed in (("amd64", "a"), ("arm64", "b")):
        payload = json.dumps({"schemaVersion": 2, "mediaType": "application/vnd.oci.image.manifest.v1+json", "config": {"mediaType": "application/vnd.oci.image.config.v1+json", "digest": "sha256:" + seed * 64, "size": 2}, "layers": []}, separators=(",", ":")).encode()
        digest = "sha256:" + hashlib.sha256(payload).hexdigest()
        child_payloads.append((digest, payload))
        descriptors.append({"mediaType": "application/vnd.oci.image.manifest.v1+json", "digest": digest, "size": len(payload), "platform": {"os": "linux", "architecture": architecture}})
        platforms.append({"os": "linux", "architecture": architecture, "digest": digest})
    index = {"schemaVersion": 2, "mediaType": "application/vnd.oci.image.index.v1+json", "manifests": descriptors}
    index_payload = json.dumps(index, separators=(",", ":")).encode()
    index_digest = "sha256:" + hashlib.sha256(index_payload).hexdigest()
    root_index = {"schemaVersion": 2, "mediaType": "application/vnd.oci.image.index.v1+json", "manifests": [{"mediaType": "application/vnd.oci.image.index.v1+json", "digest": index_digest, "size": len(index_payload), "annotations": {"org.opencontainers.image.ref.name": "stage-" + "1" * 40}}]}
    files = {"oci-layout": json.dumps({"imageLayoutVersion": "1.0.0"}).encode(), "index.json": json.dumps(root_index, separators=(",", ":")).encode(), "blobs/sha256/" + index_digest.removeprefix("sha256:"): index_payload}
    files.update({"blobs/sha256/" + digest.removeprefix("sha256:"): payload for digest, payload in child_payloads})
    with tarfile.open(path, "w") as archive:
        for name, payload in files.items():
            info = tarfile.TarInfo(name); info.size = len(payload); archive.addfile(info, io.BytesIO(payload))
    return index_digest, platforms, index_payload


def self_test(repo: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="sage-artifact-promotion-") as raw:
        temp = Path(raw)
        archive = temp / "stage.oci.tar"
        index_digest, platforms, index_payload = _fixture_archive(archive)
        stage_receipt = temp / "stage-receipt.json"
        stage_receipt.write_text(json.dumps({
            "schema_version":"1.0","record_type":"sage-portable-stage-receipt","stage_contract":"kalaxy3-portable-stage-v1",
            "source":{"git_sha":"1"*40},"artifact":{"format":"oci-layout-tar","logical_image_repository":"fixture/image","stage_tag":"stage-"+"1"*40,"archive_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"index_digest":index_digest,"index_location":"fixture","media_type":"application/vnd.oci.image.index.v1+json","platforms":platforms,"additional_manifests":[],"storage":{"provider":"github-actions-artifact","artifact_name":"fixture","artifact_id":"1","artifact_digest":"2"*64}},
            "build_contract":{"dockerfile":"yaml/nginx-docs/k8s-doc-to-nginx/nginx/Dockerfile.stage","source_validation":"make sage-stage-guardrails","documentation_validation":"make docs-mkdocs-publication-test","external_registry_credentials_used":False,"production_rebuild_permitted":False},
            "invocation":{"provider":"github-actions","workflow_run_id":"1","workflow_run_attempt":"1"},"generated_at":"2026-01-01T00:00:00Z"}, indent=2)+"\n")
        environment = temp / "environment.json"
        environment.write_text(json.dumps({
            "schema_version":"1.0","record_type":"sage-promotion-environment-manifest","environment_id":"fixture",
            "artifact_target":{"transport":"docker","repository":"registry.example/fixture/image","publication_tag_prefix":"promoted-"},
            "deployment_binding":{"kind":"ansible-kubernetes-image","playbook":"fixture.yml","receipt_variable":"sage_promotion_receipt_file","namespace":"documentation","workload":"fixture","container":"nginx"},
            "executor_contract":{"required_capabilities":["oci-archive-source","copy-all","preserve-digests","raw-inspect"],"identity_is_provenance_only":True},
            "authority":{"registry_credentials":"executor-runtime-only","secrets_in_manifest":False,"secrets_in_command_arguments":False}}, indent=2)+"\n")
        validate_promotion_inputs(stage_receipt, archive, environment)
        tool_pinned = json.loads(environment.read_text())
        tool_pinned["executor_contract"]["required_tool"] = "skopeo"
        environment.write_text(json.dumps(tool_pinned))
        try:
            validate_promotion_inputs(stage_receipt, archive, environment)
        except WorkflowError:
            pass
        else:
            raise RuntimeError("environment semantics incorrectly accepted a pinned adapter tool")
        tool_pinned["executor_contract"].pop("required_tool")
        environment.write_text(json.dumps(tool_pinned))
        validate_promotion_inputs(stage_receipt, archive, environment)
        fake = temp / "bin" / "skopeo"; fake.parent.mkdir()
        fake.write_text("""#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo 'skopeo version fixture'; exit 0; fi\nif [ \"$1\" = \"copy\" ] && [ \"$2\" = \"--help\" ]; then echo '--all --preserve-digests --digestfile'; exit 0; fi\nif [ \"$1\" = \"inspect\" ] && [ \"$2\" = \"--help\" ]; then echo '--raw'; exit 0; fi\nif [ \"$1\" = \"copy\" ]; then while [ $# -gt 0 ]; do if [ \"$1\" = \"--digestfile\" ]; then shift; printf '%s\\n' \"$FAKE_DIGEST\" > \"$1\"; fi; shift; done; exit 0; fi\nif [ \"$1\" = \"inspect\" ] && [ \"$2\" = \"--raw\" ]; then cat \"$FAKE_RAW\"; exit 0; fi\nexit 2\n""")
        fake.chmod(0o755)
        raw_manifest = temp / "raw-index.json"; raw_manifest.write_bytes(index_payload)
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = str(fake.parent) + os.pathsep + old_path
        os.environ["FAKE_DIGEST"] = index_digest
        os.environ["FAKE_RAW"] = str(raw_manifest)
        try:
            event_log = temp / "events.jsonl"
            plan = prepare_promotion(repo=repo, stage_receipt=stage_receipt, archive=archive, environment=environment, event_log=event_log, executor_id="fixture-executor", workflow_engine="fixture-engine")
            if plan["mutation_performed"] is not False:
                raise RuntimeError("prepare unexpectedly performed mutation")
            output = temp / "promotion-receipt.json"
            receipt = execute_promotion(repo=repo, stage_receipt=stage_receipt, archive=archive, environment=environment, event_log=event_log, output=output, executor_id="fixture-executor", workflow_engine="fixture-engine")
        finally:
            os.environ["PATH"] = old_path
            os.environ.pop("FAKE_DIGEST", None); os.environ.pop("FAKE_RAW", None)
        if receipt["target"]["index_digest"] != index_digest or receipt["verification"]["rebuild_performed"] is not False:
            raise RuntimeError("promotion receipt did not preserve exact digest/no-rebuild semantics")
        bad = json.loads(environment.read_text()); bad["authority"]["secrets_in_manifest"] = True; environment.write_text(json.dumps(bad))
        try:
            validate_promotion_inputs(stage_receipt, archive, environment)
        except WorkflowError:
            pass
        else:
            raise RuntimeError("environment manifest permitting secret coupling was accepted")
    print("PASS retrieved OCI archive is bound to the exact portable-stage receipt")
    print("PASS environment semantics declare capabilities without pinning an adapter tool")
    print("PASS executor qualification is capability-based and adapter identity remains provenance only")
    print("PASS promotion copies all manifests with digest preservation and independently verifies target raw digest")
    print("PASS promotion receipt binds deployment image by immutable digest and records rebuild_performed=false")
    print("Kalaxy3 SAGE artifact promotion self-test: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")
    for name in ("prepare", "execute"):
        item = sub.add_parser(name)
        item.add_argument("--stage-receipt", type=Path, required=True)
        item.add_argument("--oci-archive", type=Path, required=True)
        item.add_argument("--environment", type=Path, required=True)
        item.add_argument("--event-log", type=Path, required=True)
        item.add_argument("--executor-id", required=True)
        item.add_argument("--workflow-engine", required=True)
        if name == "execute":
            item.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test(args.repo)
    if args.command == "prepare":
        result = prepare_promotion(repo=args.repo, stage_receipt=args.stage_receipt, archive=args.oci_archive, environment=args.environment, event_log=args.event_log, executor_id=args.executor_id, workflow_engine=args.workflow_engine)
    elif args.command == "execute":
        result = execute_promotion(repo=args.repo, stage_receipt=args.stage_receipt, archive=args.oci_archive, environment=args.environment, event_log=args.event_log, output=args.output, executor_id=args.executor_id, workflow_engine=args.workflow_engine)
    else:
        raise WorkflowError("prepare or execute command is required")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, WorkflowError, ValueError) as error:
        print("Kalaxy3 SAGE artifact promotion: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
