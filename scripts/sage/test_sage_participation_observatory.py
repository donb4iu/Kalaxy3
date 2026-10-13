import json,tempfile,unittest
from pathlib import Path
from sage_participation_observatory import observe
class TestObservatory(unittest.TestCase):
    def test_empty_episode_is_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            o=observe(Path(d));self.assertFalse(o['governed_execution_verified']);self.assertEqual(len(o['unproven_roles']),11)
    def test_role_names_do_not_count(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'responsible-result.json').write_text('{}');o=observe(p)
            self.assertEqual(o['roles']['Responsible']['participation'],'not-evidenced')
    def test_receipt_presence_not_qualified(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'responsible-result.json').write_text('{}');(p/'responsible-receipt.json').write_text('{}')
            o=observe(p);self.assertEqual(o['roles']['Responsible']['participation'],'receipt-present-unqualified')
            self.assertFalse(o['functional_outcome_verified'])
    def test_forged_success_does_not_prove_outcome(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'dispatch-result.json').write_text(json.dumps({'authority':{'execution_authorized':True,'contribution_qualified':True}}))
            self.assertFalse(observe(p)['governed_execution_verified'])
if __name__=='__main__':unittest.main()
