import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from sage_engineering_dispatch import validate_candidate

class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.repo=Path(self.temp.name)
        self.content='print(1)\n'
        self.digest=hashlib.sha256(self.content.encode()).hexdigest()
        self.evidence=[{'path':'a.py','sha256':self.digest,'content':self.content}]
        self.good={'changes':[{'path':'a.py','original_sha256':self.digest,'replacement':'print(2)\n'}], 'tests':['python3 a.py']}
    def tearDown(self): self.temp.cleanup()
    def test_accept_candidate(self): self.assertEqual(len(validate_candidate(self.good,self.repo,self.evidence)),1)
    def test_missing_changes_rejected(self):
        with self.assertRaises(ValueError): validate_candidate({'changes':[], 'tests':['test']},self.repo,self.evidence)
    def test_unassigned_change_rejected(self):
        self.good['changes'][0]['path']='other.py'
        with self.assertRaises(ValueError): validate_candidate(self.good,self.repo,self.evidence)
    def test_wrong_digest_rejected(self):
        self.good['changes'][0]['original_sha256']='a'*64
        with self.assertRaises(ValueError): validate_candidate(self.good,self.repo,self.evidence)
    def test_missing_tests_rejected(self):
        self.good['tests']=[]
        with self.assertRaises(ValueError): validate_candidate(self.good,self.repo,self.evidence)

if __name__=='__main__': unittest.main()
