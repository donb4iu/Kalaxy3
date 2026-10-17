import json
import tempfile
import unittest
from pathlib import Path
from build_helper import gather, render

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.episode=self.root/'episode';self.episode.mkdir();self.dispatch=self.root/'dispatch';self.dispatch.mkdir()
        (self.episode/'objective-status.json').write_text(json.dumps({'record_type':'sage-breakglass-8020-functional-assessment','objective':'<img src=x onerror=alert(1)>','functionally_restored':False,'governed_git_integration_verified':False,'protected_architecture_helper_verified':False}))
    def tearDown(self): self.tmp.cleanup()
    def test_not_proven_and_escaped(self):
        data=gather(self.episode,self.dispatch)
        self.assertFalse(data['functional_delivery_verified']); page=render(data)
        self.assertNotIn('<img src=x',page);self.assertIn('&lt;img',page)
    def test_forged_success_flags_cannot_verify_delivery(self):
        status={'record_type':'sage-breakglass-8020-functional-assessment','objective':'Test',
                'functionally_restored':True,'governed_git_integration_verified':True,
                'protected_architecture_helper_verified':True}
        (self.episode/'objective-status.json').write_text(json.dumps(status))
        data=gather(self.episode,self.dispatch)
        self.assertFalse(data['functional_delivery_verified'])
        self.assertEqual(data['reported_status_flags']['functionally_restored'],True)
        self.assertIn('untrusted claims',render(data))

    def test_role_response_xss_escaped(self):
        (self.episode/'responsible-response.json').write_text(json.dumps({'message':'<script>alert(1)</script>'}))
        (self.episode/'responsible-receipt.json').write_text('{}')
        page=render(gather(self.episode,self.dispatch))
        self.assertNotIn('<script>alert(1)</script>',page)
        self.assertIn('&lt;script&gt;',page)

    def test_missing_role_receipt_rejected(self):
        (self.episode/'responsible-response.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'without invocation receipt'): gather(self.episode,self.dispatch)
    def test_wrong_record_type_rejected(self):
        (self.episode/'objective-status.json').write_text('{}')
        with self.assertRaises(ValueError):gather(self.episode,self.dispatch)
    def test_source_provenance_present(self):
        data=gather(self.episode,self.dispatch)
        self.assertEqual(len(data['sources']),1)
        self.assertEqual(len(data['sources'][0]['sha256']),64)

if __name__=='__main__': unittest.main()
