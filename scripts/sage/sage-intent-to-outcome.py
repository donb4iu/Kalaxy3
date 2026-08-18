
#!/usr/bin/env python3
"""Operate the repository-owned SAGE intent-to-outcome front door."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import hashlib
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import WorkflowError  # noqa: E402
from workflows.intent_to_outcome import (  # noqa: E402
    adopt_iteration,
    adopt_request_execution,
    begin_candidate_iteration,
    candidate_iteration_entry_mode,
    begin_intent,
    begin_intent_promotion,
    confirm_intent,
    continue_intent_promotion,
    continue_intent_request,
    record_runtime,
    reconcile_completed_request_child,
    reconcile_completed_semantic_child,
    validate_runtime_receipt,
)


def self_test() -> int:
    good = {
        "schema_version": "1.0",
        "record_type": "sage-e2e-zero-trust-runtime-receipt",
        "status": "pass",
        "checks": {
            "workload_ready": True,
            "origin_through_traefik_ready": True,
            "tunnel_ready": True,
            "connector_node_ha": True,
            "metrics_monitor_configured": True,
            "unauthenticated_access_denied": True,
            "authorized_mfa_access_verified": True,
            "privileged_surfaces_not_published": True,
        },
        "value_vignette": {
            "architect_observation": "Architect delegated Kubernetes Cloudflare installation knowledge to SAGE.",
            "sage_finding": "SAGE found the deployment entry point could not decrypt its required Ansible Vault.",
            "prevented_action": "SAGE blocked credential introduction and cluster mutation before deployment.",
            "bounded_correction": "The existing interactive Ansible Vault decryption convention was reused.",
            "value_demonstrated": "SAGE carried implementation burden and detected a cross-component integration gap.",
        },
    }
    validate_runtime_receipt(good)
    bad = json.loads(json.dumps(good))
    bad["checks"]["authorized_mfa_access_verified"] = False
    try:
        validate_runtime_receipt(bad)
    except WorkflowError:
        pass
    else:
        raise RuntimeError("missing MFA runtime proof was accepted")
    missing_vignette = json.loads(json.dumps(good))
    missing_vignette.pop("value_vignette")
    try:
        validate_runtime_receipt(missing_vignette)
    except WorkflowError:
        pass
    else:
        raise RuntimeError("runtime receipt without the SAGE value vignette was accepted")
    bad_node_ha = json.loads(json.dumps(good))
    bad_node_ha["checks"]["connector_node_ha"] = False
    try:
        validate_runtime_receipt(bad_node_ha)
    except WorkflowError:
        pass
    else:
        raise RuntimeError("runtime receipt without connector node-level HA was accepted")
    print("PASS runtime acceptance requires MFA, negative-access proof, and connector node-level HA")
    print("PASS runtime acceptance requires the SAGE value vignette")

    with tempfile.TemporaryDirectory(prefix="sage-intent-completed-child-") as temp_name:
        temp = Path(temp_name)
        request = "fixture completed child request"
        request_sha = hashlib.sha256(request.encode("utf-8")).hexdigest()
        receipt = temp / "routine-git-lifecycle-receipt.json"
        receipt.write_text(json.dumps({"schema_version": "fixture", "status": "pass"}) + "\n", encoding="utf-8")
        receipt_sha = hashlib.sha256(receipt.read_bytes()).hexdigest()
        verification = temp / "post-operator-verification.json"
        metrics = temp / "outcome-metrics.json"
        closeout = temp / "closeout.json"
        for path in (verification, metrics, closeout):
            path.write_text(json.dumps({"status": "pass"}) + "\n", encoding="utf-8")
        child = temp / "request-execution-state.json"
        child.write_text(
            json.dumps(
                {
                    "record_type": "sage-request-execution-state",
                    "request_sha256": request_sha,
                    "current_boundary": "complete",
                    "current_proposal": None,
                    "history": [
                        {
                            "boundary": "routine-git-lifecycle",
                            "boundary_result_sha256": receipt_sha,
                            "verification": str(verification),
                            "metrics": str(metrics),
                            "evidence_closeout": str(closeout),
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        reconciled = reconcile_completed_request_child(
            {"request_sha256": request_sha}, child, routine_receipt=receipt
        )
        if reconciled.get("status") != "complete" or reconciled.get("reconciled_from_completed_child") is not True:
            raise RuntimeError("completed child reconciliation did not return complete evidence")
        bad_receipt = temp / "other-receipt.json"
        bad_receipt.write_text("{}\n", encoding="utf-8")
        try:
            reconcile_completed_request_child(
                {"request_sha256": request_sha}, child, routine_receipt=bad_receipt
            )
        except WorkflowError:
            pass
        else:
            raise RuntimeError("non-canonical completed-child routine receipt was accepted")
    print("PASS already-completed self-closing request child reconciles without replay")
    with tempfile.TemporaryDirectory(prefix="sage-semantic-child-reconcile-") as raw:
        temp = Path(raw)
        contribution = temp / "contribution.zip"
        contribution.write_bytes(b"fixture")
        dispositions = temp / "dispositions.json"
        dispositions.write_text("{}\n", encoding="utf-8")
        planning_source = temp / "source.zip"
        planning_source.write_bytes(b"planning")
        semantic_state = temp / "state.json"
        semantic_state.write_text(
            json.dumps({
                "schema_version": "1.0",
                "record_type": "sage-semantic-bootstrap-state",
                "action_id": "SAGE-ACTION-FIXTURE",
                "request": "fixture request",
                "contribution": str(contribution),
                "semantic_understanding_sha256": "a" * 64,
                "architect_dispositions_sha256": hashlib.sha256(dispositions.read_bytes()).hexdigest(),
                "planning_source": str(planning_source),
                "status": "planning-source-ready",
            }) + "\n",
            encoding="utf-8",
        )
        reconciled_semantic = reconcile_completed_semantic_child(
            {
                "request": "fixture request",
                "action_id": "SAGE-ACTION-FIXTURE",
                "contribution": str(contribution),
            },
            semantic_state,
            "a" * 64,
            dispositions,
            "architect",
        )
        if reconciled_semantic.get("planning_source") != str(planning_source.resolve()) or reconciled_semantic.get("reconciled_from_completed_semantic_child") is not True:
            raise RuntimeError("completed semantic child did not reconcile planning-source lineage")
    print("PASS already-completed semantic child reconciles without replay")
    if candidate_iteration_entry_mode("source-git-complete") != "durable-checkpoint":
        raise RuntimeError("durable candidate checkpoint classification failed")
    if candidate_iteration_entry_mode("architect-confirmation-required") != "inflight-supersession":
        raise RuntimeError("pre-mutation candidate could not accumulate a related correction")
    if candidate_iteration_entry_mode("planning-source-ready") != "inflight-supersession":
        raise RuntimeError("planning-gap candidate could not re-enter without replaying semantic confirmation")
    try:
        candidate_iteration_entry_mode("request-operator-review-required")
    except WorkflowError:
        pass
    else:
        raise RuntimeError("live operator-review boundary was silently superseded")
    print("PASS unfinished pre-mutation candidate can accumulate related corrections before checkpoint")
    print("PASS live operator-review boundary remains fail-closed")
    print("PASS intent-to-outcome front door self-test")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    start = sub.add_parser("start")
    start.add_argument("--request", required=True)
    start.add_argument("--action-id", required=True)
    start.add_argument("--contribution", type=Path, required=True)

    confirm = sub.add_parser("confirm")
    confirm.add_argument("--state", type=Path, required=True)
    confirm.add_argument("--confirmation", required=True)
    confirm.add_argument("--dispositions", type=Path, required=True)
    confirm.add_argument("--actor", required=True)

    adopt = sub.add_parser("adopt-request")
    adopt.add_argument("--request", required=True)
    adopt.add_argument("--request-state", type=Path, required=True)

    adopt_iteration_parser = sub.add_parser("adopt-iteration")
    adopt_iteration_parser.add_argument("--request", required=True)
    adopt_iteration_parser.add_argument("--request-state", type=Path, required=True)
    adopt_iteration_parser.add_argument("--action-id")
    adopt_iteration_parser.add_argument("--candidate-head")
    adopt_iteration_parser.add_argument("--planning-source", type=Path)
    adopt_iteration_parser.add_argument("--unresolved-finding", action="append", default=[])

    iterate = sub.add_parser("iterate")
    iterate.add_argument("--state", type=Path, required=True)
    iterate.add_argument("--contribution", type=Path, required=True)
    iterate.add_argument("--trigger", required=True)
    iterate.add_argument(
        "--reentry-boundary",
        choices=("implementation-local", "planning", "semantic-confirmation", "authority"),
        required=True,
    )
    iterate.add_argument("--parent-checkpoint", required=True)
    iterate.add_argument("--affected-obligation", action="append", default=[])
    iterate.add_argument("--approved-gap-set", type=Path)

    continuation = sub.add_parser("continue-request")
    continuation.add_argument("--state", type=Path, required=True)
    continuation.add_argument("--operator-result", type=Path)
    continuation.add_argument("--routine-receipt", type=Path)

    runtime = sub.add_parser("record-runtime")
    runtime.add_argument("--state", type=Path, required=True)
    runtime.add_argument("--runtime-receipt", type=Path, required=True)

    promote = sub.add_parser("promote")
    promote.add_argument("--state", type=Path, required=True)
    promote.add_argument("--expected-head", required=True)
    promote.add_argument("--title", required=True)
    promote.add_argument("--body", required=True)

    promotion = sub.add_parser("continue-promotion")
    promotion.add_argument("--state", type=Path, required=True)
    promotion.add_argument("--operator-result", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    if args.command == "start":
        result = begin_intent(args.repo, args.action_id, args.request, args.contribution)
    elif args.command == "confirm":
        result = confirm_intent(
            args.repo, args.state, args.confirmation, args.dispositions, args.actor
        )
    elif args.command == "adopt-request":
        result = adopt_request_execution(args.repo, args.request, args.request_state)
    elif args.command == "adopt-iteration":
        result = adopt_iteration(
            args.repo,
            args.request,
            args.request_state,
            action_id=args.action_id,
            candidate_head=args.candidate_head,
            planning_source=args.planning_source,
            unresolved_findings=args.unresolved_finding,
        )
    elif args.command == "iterate":
        result = begin_candidate_iteration(
            args.repo,
            args.state,
            args.contribution,
            trigger=args.trigger,
            reentry_boundary=args.reentry_boundary,
            parent_checkpoint=args.parent_checkpoint,
            affected_obligations=args.affected_obligation,
            approved_gap_set=args.approved_gap_set,
        )
    elif args.command == "continue-request":
        result = continue_intent_request(
            args.repo,
            args.state,
            operator_result=args.operator_result,
            routine_receipt=args.routine_receipt,
        )
    elif args.command == "record-runtime":
        result = record_runtime(args.state, args.runtime_receipt)
    elif args.command == "promote":
        result = begin_intent_promotion(
            args.repo, args.state, args.expected_head, args.title, args.body
        )
    elif args.command == "continue-promotion":
        result = continue_intent_promotion(
            args.repo, args.state, args.operator_result
        )
    else:
        raise WorkflowError("one intent-to-outcome command is required")
    print("Kalaxy3 SAGE intent-to-outcome: PASS")
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, RuntimeError, WorkflowError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE intent-to-outcome: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
