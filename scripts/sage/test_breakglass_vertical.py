"""Regression for independent Referee participation and repository-owned digests."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

ROOT = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerticalTests(TestCase):
    def test_bad_model_digest_is_replaced_by_repository_evidence(self):
        readiness = load('fresh_role_readiness')
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sample.py').write_text('safe\n')
            result = readiness._validate_grounding(
                [{'path': 'sample.py', 'sha256': 'INVALID'}], root
            )
            self.assertEqual(result[0]['sha256'], readiness.sha256_file(root / 'sample.py'))
            self.assertEqual(result[0]['model_digest_disposition'], 'ignored-invalid')

    def test_escape_path_fails_closed(self):
        readiness = load('fresh_role_readiness')
        with TemporaryDirectory() as folder:
            with self.assertRaises(readiness.ReadinessError):
                readiness._validate_grounding([{'path': '../escape.py'}], Path(folder))

    def test_well_formed_wrong_hash_still_rejected(self):
        readiness = load('fresh_role_readiness')
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sample.py').write_text('safe\n')
            with self.assertRaises(readiness.ReadinessError):
                readiness._validate_grounding(
                    [{'path': 'sample.py', 'sha256': '0' * 64}], root
                )

    def test_referee_allow(self):
        gate = load('sage_referee_gate')
        with mock.patch.dict('sys.modules', {'llm_role_invocation': mock.Mock()}):
            import sys
            sys.modules['llm_role_invocation'].invoke_ollama_json.return_value = (
                {'verdict': 'allow', 'findings': [], 'rationale': 'preserved'}, {'model': 'test'}
            )
            result = gate.assess('functional goal', {'decision': 'plan'}, 'endpoint', 'model')
            self.assertEqual(result['decision']['verdict'], 'allow')

    def test_referee_invalid_response_fails_closed(self):
        gate = load('sage_referee_gate')
        with mock.patch.dict('sys.modules', {'llm_role_invocation': mock.Mock()}):
            import sys
            sys.modules['llm_role_invocation'].invoke_ollama_json.return_value = ({}, {})
            with self.assertRaises(gate.RefereeError):
                gate.assess('functional goal', {}, 'endpoint', 'model')
