#!/usr/bin/env python3
"""Fail-closed static guardrail for the staged Issue #50 Helm deployment."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


LOCK_ENTRY: dict[str, str] = {
    'chart': 'neo4j/neo4j',
    'enabled_variable': 'sage_neo4j_deploy_authorized',
    'namespace': 'sage',
    'release': 'sage-neo4j',
    'version': '2026.10.1',
}
REPO_ENTRY: dict[str, str] = {
    'name': 'neo4j', 'url': 'https://helm.neo4j.com/neo4j',
    'url_sha256': hashlib.sha256(
        b'https://helm.neo4j.com/neo4j').hexdigest(),
}


def read_json(path: Path) -> Any:
    """Read JSON from the specified repository path.

    Args:
        path: File containing a JSON document.
    """
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition: bool, diagnostic: str) -> None:
    """Fail closed when an infrastructure contract cannot be confirmed.

    Args:
        condition: A statically verifiable safety property.
        diagnostic: Actionable error identifier.
    """
    if not condition:
        raise ValueError(diagnostic)


def audit(root: Path) -> dict[str, str]:
    """Validate guarded, pinned, LAN-only load-balancer configuration.

    Args:
        root: Kalaxy3 repository root.
    """
    infra = root / 'infrastructure/k3s-homelab'
    lock = read_json(infra / 'helm-chart-lock.json')
    repos = read_json(infra / 'helm-repositories.json')
    require(lock.get('charts', {}).get('sage_neo4j') == LOCK_ENTRY,
            'ISSUE50_CHART_LOCK_MISMATCH')
    require(REPO_ENTRY in repos.get('repositories', []),
            'ISSUE50_HELM_REPOSITORY_MISSING')
    values = (infra / 'helm-values/sage-neo4j.yaml').read_text('utf-8')
    phase = (infra / 'playbooks/platform.yml').read_text('utf-8')
    tasks = (infra / 'playbooks/tasks/sage-neo4j.yml').read_text('utf-8')
    require(re.search(
        r'(?ms)^services:\n  neo4j:\n    enabled: true\n'
        r'    spec:\n      type: LoadBalancer\n', values) is not None,
        'ISSUE50_LAN_LOADBALANCER_REQUIRED')
    for port, allowed in (('http', False), ('https', True),
                          ('bolt', True), ('backup', False)):
        require(re.search(
            rf'(?m)^      {port}:\n        enabled: {str(allowed).lower()}$',
            values) is not None,
            f'ISSUE50_{port.upper()}_PORT_POLICY_VIOLATION')
    require('passwordFromSecret: sage-neo4j-auth' in values and
            'storageClassName: longhorn' in values and
            'edition: community' in values,
            'ISSUE50_COMMUNITY_STORAGE_SECRET_CONTRACT_MISSING')
    require('false  # Staged only; explicit governed activation required' in phase,
            'ISSUE50_STAGED_ACTIVATION_BLOCK_MISSING')
    require('sage_neo4j_deploy_authorized | default(false) | bool' in phase and
            "selected_platform_phase == 'sage_neo4j'" in phase,
            'ISSUE50_PLATFORM_PHASE_NOT_GATED')
    require("selected_platform_phase in ['all', 'sage_neo4j']" not in phase,
            'ISSUE50_ALL_PHASE_MUST_NOT_DEPLOY')
    require('sage_neo4j_deploy_authorized | default(false) | bool' in tasks and
            "selected_platform_phase == 'sage_neo4j'" in tasks,
            'ISSUE50_TASK_AUTHORITY_GATE_MISSING')
    require('helm_chart_lock.charts.sage_neo4j.version' in tasks and
            'sage-neo4j-auth' in tasks and '--install' in tasks,
            'ISSUE50_HELM_DEPLOYMENT_NOT_PINNED')
    require('password:' not in values and 'loadBalancerIP:' not in values,
            'ISSUE50_SECRET_OR_UNRECONCILED_IP')
    return {'result': 'PASS', 'phase': 'sage_neo4j',
            'deployment_authorized': 'false', 'chart_version': LOCK_ENTRY['version'],
            'access': 'LAN_MetalLB_Bolt_HTTPS', 'external_ip': 'not_assigned'}


def main() -> int:
    """Run the static guardrail against a specific repository root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.repo), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
