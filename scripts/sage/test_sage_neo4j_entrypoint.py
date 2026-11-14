"""Regression tests for the existing Neo4j projection CLI default source."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from typing import Any


class ProjectionEntrypointTests(unittest.TestCase):
    """Check single-revision startup and retention of existing CLI options."""

    def setUp(self) -> None:
        """Load the CLI and make a Git fixture with no main branch."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        cli_path = Path(__file__).with_name('sage-neo4j-projection.py')
        spec = importlib.util.spec_from_file_location('sage_cli', cli_path)
        if spec is None or spec.loader is None:
            raise RuntimeError('UNAVAILABLE_PROJECTION_CLI')
        self.cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.cli)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Issue50 Fixture')
        self.git('checkout', '-qb', 'feature/issue50')
        (self.repo / 'SAGE.md').write_text('# SAGE\n', encoding='utf-8')
        (self.repo / 'subject.md').write_text('# Subject\n', encoding='utf-8')
        (self.repo / 'opaque.bin').write_bytes(b'\x00\xff')
        self.git('add', '-A')
        self.git('commit', '-qm', 'feature-only evidence')

    def git(self, *args: str) -> str:
        """Run Git inside the disposable test repository.

        Args:
            args: Git arguments.
        """
        return subprocess.check_output(
            ['git', '-C', str(self.repo), *args], text=True
        ).strip()

    def cli_args(self, config: Path | None = None) -> argparse.Namespace:
        """Create an offline CLI request without Neo4j integration.

        Args:
            config: Optional legacy concept-file path.
        """
        return argparse.Namespace(repo=self.repo, out=self.repo / 'receipts',
                                  config=config, require_integration=False)

    def test_no_config_uses_complete_single_revision(self) -> None:
        """Construct projection from feature-only Git without a vocabulary."""
        result: dict[str, Any] = self.cli.run(self.cli_args())
        self.assertEqual(result['source_revision'], self.git('rev-parse', 'HEAD'))
        self.assertEqual(result['source_count'], 3)
        self.assertGreaterEqual(result['concept_count'], 1)
        self.assertGreaterEqual(result['candidate_links'], 3)
        self.assertEqual(result['neo4j'], 'not_run_requires_local_integration')

    def test_explicit_config_remains_supported(self) -> None:
        """Forward explicit vocabulary input without deriving a Git snapshot."""
        alias = self.repo / 'repo-alias'
        alias.symlink_to(self.repo, target_is_directory=True)
        self.repo = alias
        config = self.repo / 'explicit-concepts.json'
        fake = {'sources': [{'path': 'SAGE.md'}], 'concepts': [],
                'candidate_edges': [], 'revision': 'commit'}
        with patch.object(self.cli, 'prepare', return_value=fake) as prepare:
            with patch.object(self.cli, 'ensure_lossless'):
                with patch.object(self.cli, 'projection_id', return_value='p'):
                    self.cli.run(self.cli_args(config))
        prepare.assert_called_once_with(self.repo.resolve(), config)

    def test_existing_navigation_arguments_remain_available(self) -> None:
        """Preserve objective-scoped and inventory navigation options."""
        argv = ['cli', '--repo', str(self.repo), '--out', str(self.repo),
                '--objective', 'Show source evidence', '--browse-inventory']
        with patch.object(sys, 'argv', argv):
            args = self.cli.arguments()
        self.assertEqual(args.objective, 'Show source evidence')
        self.assertTrue(args.browse_inventory)


if __name__ == '__main__':
    unittest.main()
