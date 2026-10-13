import tempfile, unittest
from pathlib import Path
from sage_delegation_contract import required_source_records, combine_role_context, EvidenceSelectionError

class EvidenceTests(unittest.TestCase):
    def test_exact_source_and_digest(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'x.py').write_text('print(1)\n')
            rows=required_source_records(root,{'evidence_paths':['x.py']})
            self.assertEqual(rows[0]['content'],'print(1)\n')
            self.assertEqual(len(rows[0]['sha256']),64)
    def test_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(EvidenceSelectionError):
                required_source_records(Path(td),{'evidence_paths':['absent.py']})
    def test_escaping_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(EvidenceSelectionError):
                required_source_records(Path(td),{'evidence_paths':['../secret']})
    def test_required_over_budget_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'huge.py').write_text('x'*1000)
            with self.assertRaises(EvidenceSelectionError):
                required_source_records(root,{'evidence_paths':['huge.py']}, max_chars=30)
    def test_required_first_and_dedup(self):
        req={'path':'x.py','content':'required'}
        value=combine_role_context({'repository_files':[{'path':'x.py','content':'other'},{'path':'y.py','content':'generic'}]},[req])
        self.assertEqual(value['repository_files'][0],req)
        self.assertEqual(len(value['repository_files']),2)
    def test_front_door_integration(self):
        source=(Path(__file__).parent/'sage-intent-front-door.py').read_text()
        self.assertIn('required_source_records(repo_path, assignment)',source)
        self.assertIn('combine_role_context(selected_context, required_records)',source)
