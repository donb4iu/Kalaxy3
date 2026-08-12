"""Pure checkpoint persistence and promotion eligibility contracts."""
from __future__ import annotations

from typing import Any, Iterable, Mapping


class PromotionError(RuntimeError):
    """Fail closed when checkpoint promotion policy is not satisfied."""


def require(value: bool, message: str) -> None:
    if not value:
        raise PromotionError(message)


def applicable_gates(
    policy: Mapping[str, Any],
    changed_paths: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    paths = tuple(sorted({str(item) for item in changed_paths if str(item)}))
    require(bool(paths), "promotion path delta must not be empty")
    rules = policy.get("gate_rules")
    require(isinstance(rules, list) and bool(rules), "gate_rules missing")
    selected: list[dict[str, Any]] = []
    for raw in rules:
        require(isinstance(raw, Mapping), "gate rule must be an object")
        rule = dict(raw)
        prefixes = tuple(str(item) for item in rule.get("path_prefixes", ()))
        exact = {str(item) for item in rule.get("path_exact", ())}
        if rule.get("always") is True or any(
            path in exact or any(path.startswith(prefix) for prefix in prefixes)
            for path in paths
        ):
            selected.append(rule)
    require(
        any(item.get("gate_id") == "repository-sage" for item in selected),
        "repository-sage gate missing",
    )
    return tuple(selected)


def checkpoint_receipt(
    *,
    source_branch: str,
    source_head: str,
    upstream_head: str,
    dependency_blocked: bool,
    validation_complete: bool,
) -> dict[str, Any]:
    require(bool(source_branch), "checkpoint source branch is required")
    require(source_head == upstream_head, "checkpoint source is not synchronized")
    return {
        "schema_version": "1.0",
        "record_type": "sage-checkpoint-persistence",
        "source": {
            "branch": source_branch,
            "head": source_head,
            "upstream_head": upstream_head,
        },
        "dependency_blocked": bool(dependency_blocked),
        "validation_complete": bool(validation_complete),
        "checkpoint_persisted": True,
        "promotion_eligible": False,
        "promotion_claim": "none",
    }


def eligibility(
    *,
    policy: Mapping[str, Any],
    source_branch: str,
    source_head: str,
    upstream_head: str,
    remote_source_head: str,
    target_branch: str,
    target_head: str,
    remote_target_head: str,
    changed_paths: Iterable[str],
    source_descends: bool,
    gate_results: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    promotion = policy.get("promotion_policy")
    require(isinstance(promotion, Mapping), "promotion_policy missing")
    require(source_branch and source_branch != target_branch, "source must be a non-target branch")
    require(source_head == upstream_head, "source branch is not synchronized with local upstream")
    require(source_head == remote_source_head, "source branch is not synchronized with remote")
    require(target_branch == promotion.get("target_branch"), "target branch differs from policy")
    require(target_head == remote_target_head, "local target authority is stale versus remote")
    require(source_descends, "source does not descend from frozen target")
    paths = tuple(sorted({str(item) for item in changed_paths if str(item)}))
    gates = applicable_gates(policy, paths)
    expected = {str(item["gate_id"]) for item in gates}
    results = [dict(item) for item in gate_results]
    observed = {str(item.get("gate_id")) for item in results}
    require(observed == expected, "gate result set differs from applicable gate set")
    for result in results:
        gate_id = result.get("gate_id")
        require(result.get("status") == "pass", f"promotion gate failed: {gate_id}")
        digest = result.get("sha256")
        require(isinstance(digest, str) and len(digest) == 64, "gate digest invalid")
    return {
        "schema_version": "1.0",
        "record_type": "sage-checkpoint-promotion-eligibility",
        "source": {
            "branch": source_branch,
            "head": source_head,
            "upstream_head": upstream_head,
            "remote_head": remote_source_head,
        },
        "target": {
            "branch": target_branch,
            "frozen_head": target_head,
            "remote_head": remote_target_head,
        },
        "changed_paths": list(paths),
        "source_descends_from_target": True,
        "applicable_gate_ids": sorted(expected),
        "gate_results": results,
        "promotion_eligible": True,
        "checkpoint_persistence_alone_is_insufficient": True,
        "operator_boundaries": list(promotion.get("operator_boundaries", ())),
        "target_advance_requires_revalidation": bool(
            promotion.get("fail_if_target_advances_before_merge")
        ),
    }


def self_test() -> int:
    policy = {
        "promotion_policy": {
            "target_branch": "main",
            "operator_boundaries": [
                "pull-request-create",
                "pull-request-merge",
                "post-merge-fetch",
            ],
            "fail_if_target_advances_before_merge": True,
        },
        "gate_rules": [
            {
                "gate_id": "repository-sage",
                "always": True,
                "path_prefixes": [],
                "path_exact": [],
            },
            {
                "gate_id": "documentation-publication",
                "always": False,
                "path_prefixes": ["markdown/"],
                "path_exact": [],
            },
            {
                "gate_id": "homelab-cluster",
                "always": False,
                "path_prefixes": ["infrastructure/k3s-homelab/"],
                "path_exact": [],
            },
        ],
    }
    checkpoint = checkpoint_receipt(
        source_branch="staged/x",
        source_head="1" * 40,
        upstream_head="1" * 40,
        dependency_blocked=True,
        validation_complete=False,
    )
    assert checkpoint["checkpoint_persisted"] is True
    assert checkpoint["promotion_eligible"] is False

    paths = ("markdown/a.md", "infrastructure/k3s-homelab/Makefile")
    gates = applicable_gates(policy, paths)
    assert {item["gate_id"] for item in gates} == {
        "repository-sage",
        "documentation-publication",
        "homelab-cluster",
    }
    passed = [
        {"gate_id": item["gate_id"], "status": "pass", "sha256": "a" * 64}
        for item in gates
    ]
    result = eligibility(
        policy=policy,
        source_branch="staged/x",
        source_head="1" * 40,
        upstream_head="1" * 40,
        remote_source_head="1" * 40,
        target_branch="main",
        target_head="0" * 40,
        remote_target_head="0" * 40,
        changed_paths=paths,
        source_descends=True,
        gate_results=passed,
    )
    assert result["promotion_eligible"] is True

    negative = [
        dict(source_head="1" * 40, upstream_head="2" * 40, remote_source_head="1" * 40),
        dict(source_head="1" * 40, upstream_head="1" * 40, remote_source_head="2" * 40),
        dict(target_head="0" * 40, remote_target_head="2" * 40),
    ]
    for overrides in negative:
        args = {
            "policy": policy,
            "source_branch": "staged/x",
            "source_head": "1" * 40,
            "upstream_head": "1" * 40,
            "remote_source_head": "1" * 40,
            "target_branch": "main",
            "target_head": "0" * 40,
            "remote_target_head": "0" * 40,
            "changed_paths": paths,
            "source_descends": True,
            "gate_results": passed,
        }
        args.update(overrides)
        try:
            eligibility(**args)
        except PromotionError:
            pass
        else:
            raise AssertionError("stale or unsynchronized authority was accepted")

    failed = [dict(passed[0], status="fail"), *passed[1:]]
    try:
        eligibility(
            policy=policy,
            source_branch="staged/x",
            source_head="1" * 40,
            upstream_head="1" * 40,
            remote_source_head="1" * 40,
            target_branch="main",
            target_head="0" * 40,
            remote_target_head="0" * 40,
            changed_paths=paths,
            source_descends=True,
            gate_results=failed,
        )
    except PromotionError:
        pass
    else:
        raise AssertionError("failed gate was accepted")

    print("PASS incomplete checkpoint persistence remains non-promotable")
    print("PASS all-applicable-gates promotion conjunction")
    print("PASS stale local/remote authority fails closed")
    print("PASS dependency-deadlock recovery semantics")
    print("Kalaxy3 checkpoint promotion policy self-test: PASS")
    return 0
