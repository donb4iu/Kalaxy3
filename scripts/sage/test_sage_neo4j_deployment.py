#!/usr/bin/env python3
"""Test the Issue #50 Ansible deployment's mandatory no-deploy boundary."""

from __future__ import annotations

import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sage_neo4j_deployment_guardrail import audit


class DeploymentGuardrailTests(unittest.TestCase):
    """Exercise fail-closed configuration checks with local fixture files."""

    def setUp(self) -> None:
        """Reconstruct the smallest valid on-branch deployment configuration."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        infra = self.root / 'infrastructure/k3s-homelab'
        self.infra = infra
        (infra / 'helm-values').mkdir(parents=True)
        (infra / 'playbooks/tasks').mkdir(parents=True)
        source = Path(__file__).resolve().parents[2] / 'infrastructure/k3s-homelab'
        for sub in ('helm-values/sage-neo4j.yaml',
                    'playbooks/tasks/sage-neo4j.yml'):
            (infra / sub).write_bytes((source / sub).read_bytes())
        (infra / 'playbooks/platform.yml').write_text(
            "tasks:\n  - name: \"Run Issue #50 Neo4j phase (separately authorized only)\"\n"
            '    ansible.builtin.include_tasks: tasks/sage-neo4j.yml\n'
            "    when:\n      - false  # Staged only; explicit governed activation required\n"
            "      - selected_platform_phase == 'sage_neo4j'\n"
            '      - sage_neo4j_deploy_authorized | default(false) | bool\n',
            encoding='utf-8')
        (infra / 'helm-chart-lock.json').write_text(json.dumps({
            'charts': {'sage_neo4j': {
                'chart': 'neo4j/neo4j', 'enabled_variable': 'sage_neo4j_deploy_authorized',
                'namespace': 'sage', 'release': 'sage-neo4j', 'version': '2026.10.1'}}}),
            encoding='utf-8')
        (infra / 'helm-repositories.json').write_text(json.dumps({
            'repositories': [{'name': 'neo4j', 'url': 'https://helm.neo4j.com/neo4j',
                              'url_sha256': hashlib.sha256(
                                  b'https://helm.neo4j.com/neo4j').hexdigest()}]}),
            encoding='utf-8')

    def test_staged_config_passes(self) -> None:
        """Accept a gated chart exposing approved LAN ports."""
        self.assertEqual(audit(self.root)['result'], 'PASS')

    def test_disabled_lan_access_rejected(self) -> None:
        """Reject disabling the Architect-agreed LAN service."""
        path = self.infra / 'helm-values/sage-neo4j.yaml'
        path.write_text(path.read_text('utf-8').replace(
            'neo4j:\n    enabled: true', 'neo4j:\n    enabled: false'), 'utf-8')
        with self.assertRaisesRegex(ValueError, 'LAN_LOADBALANCER'):
            audit(self.root)

    def test_public_http_port_rejected(self) -> None:
        """Reject plaintext HTTP publication on the LAN load balancer."""
        path = self.infra / 'helm-values/sage-neo4j.yaml'
        path.write_text(path.read_text('utf-8').replace(
            'http:\n        enabled: false', 'http:\n        enabled: true'), 'utf-8')
        with self.assertRaisesRegex(ValueError, 'HTTP_PORT'):
            audit(self.root)

    def test_backup_port_rejected(self) -> None:
        """Reject the unauthenticated backup listener on the LAN service."""
        path = self.infra / 'helm-values/sage-neo4j.yaml'
        path.write_text(path.read_text('utf-8').replace(
            'backup:\n        enabled: false', 'backup:\n        enabled: true'), 'utf-8')
        with self.assertRaisesRegex(ValueError, 'BACKUP_PORT'):
            audit(self.root)

    def test_nodeport_substitution_rejected(self) -> None:
        """Detect a silent change from MetalLB to a NodePort service."""
        path = self.infra / 'helm-values/sage-neo4j.yaml'
        path.write_text(path.read_text('utf-8').replace(
            'type: LoadBalancer', 'type: NodePort'), 'utf-8')
        with self.assertRaisesRegex(ValueError, 'LAN_LOADBALANCER'):
            audit(self.root)

    def test_default_platform_deployment_rejected(self) -> None:
        """Reject including the database in an ordinary platform all phase."""
        path = self.infra / 'playbooks/platform.yml'
        path.write_text(path.read_text('utf-8') +
                        "    selected_platform_phase in ['all', 'sage_neo4j']\n", 'utf-8')
        with self.assertRaisesRegex(ValueError, 'ALL_PHASE'):
            audit(self.root)

    def test_unapproved_activation_rejected(self) -> None:
        """Require an independent code change before deployment can activate."""
        path = self.infra / 'playbooks/platform.yml'
        path.write_text(path.read_text('utf-8').replace(
            '      - false  # Staged only; explicit governed activation required\n', ''),
            'utf-8')
        with self.assertRaisesRegex(ValueError, 'ACTIVATION_BLOCK'):
            audit(self.root)

    def test_unpinned_chart_rejected(self) -> None:
        """Reject drift away from the repository-locked chart revision."""
        path = self.infra / 'helm-chart-lock.json'
        doc = json.loads(path.read_text('utf-8'))
        doc['charts']['sage_neo4j']['version'] = 'latest'
        path.write_text(json.dumps(doc), 'utf-8')
        with self.assertRaisesRegex(ValueError, 'CHART_LOCK'):
            audit(self.root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
