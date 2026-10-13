"""Regression tests for context fidelity and bounded assignment."""
import json
import tempfile
import unittest
from pathlib import Path
from sage_delegation_contract import AssignmentError, bounded_role_context, load_assignment


class DelegationTests(unittest.TestCase):
    def test_default_deliverable_preserved(self):
        self.assertEqual(load_assignment('', 'Implement working path')['deliverable'], 'Implement working path')

    def test_explicit_assignment_and_constraints(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'a.json'
            p.write_text(json.dumps({'deliverable':'Actual source changes', 'acceptance':['tests pass']}))
            self.assertEqual(load_assignment(str(p),'Parent objective')['acceptance'], ['tests pass'])

    def test_missing_deliverable_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'a.json'
            p.write_text('{"acceptance": []}')
            with self.assertRaises(AssignmentError):
                load_assignment(str(p),'Objective')

    def test_selected_files_reach_envelope(self):
        original = {'contexts':['core'], 'repository_files':[{'path':'a.py', 'sha256':'a'*64}], 'evidence_retrieval':{}}
        projection = bounded_role_context(original)
        self.assertEqual(projection['repository_files'][0]['path'],'a.py')

    def test_budget_avoids_overload(self):
        original = {'repository_files':[{'text':'x'*100000}]}
        projection = bounded_role_context(original, max_chars=1000)
        self.assertTrue(projection['truncated'])
        self.assertEqual(projection['repository_files'],[])

    def test_integrated_front_door_carries_context_and_assignment(self):
        src = (Path(__file__).parent/'sage-intent-front-door.py').read_text()
        self.assertIn('"selected_repository_context": role_context',src)
        self.assertIn('"assignment": assignment',src)
        self.assertIn('assignment=assignment',src)

    def test_referee_enforces_deliverable_fidelity(self):
        src = (Path(__file__).parent/'sage_referee_gate.py').read_text()
        self.assertIn('A harmless but off-target response is a fidelity failure',src)


if __name__ == '__main__':
    unittest.main()
