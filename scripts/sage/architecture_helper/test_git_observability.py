import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import git_observability as g

class GitProjectionTests(unittest.TestCase):
    def test_integration_and_wip(self):
        with patch.object(g,'branch_snapshot',return_value=('a'*40,[{'branch':'main','sha':'a'*40,'commit_time':'x','subject':'merged','ahead':0,'behind':0,'integrated':True},{'branch':'feature/one','sha':'b'*40,'commit_time':'x','subject':'work','ahead':2,'behind':1,'integrated':False}])),patch.object(g,'github_prs',return_value=([{'number':8,'branch':'feature/one','title':'work','url':'https://example.com','base':'main','draft':False,'updated_at':'x'}],'available')):
            d=g.make_projection('.',generated_at='2026-10-18T10:00:00Z')
        self.assertEqual(d['main_sha'],'a'*40)
        self.assertEqual(d['branches'][1]['open_prs'],[8])
        self.assertIn('Published work in progress',g.render(d))
        self.assertNotIn('runtime proven',g.render(d).lower())
    def test_no_pr_credentials_is_not_gate(self):
        with patch.object(g,'branch_snapshot',return_value=('a'*40,[])):
            d=g.make_projection('.',repo_slug='owner/repo',token=None)
        self.assertIn('unavailable',d['pr_status'])
    def test_git_failure_is_not_gate(self):
        with patch.object(g,'branch_snapshot',side_effect=__import__('subprocess').CalledProcessError(1,['git'])),patch.object(g,'github_prs',return_value=([],'unavailable')):
            d=g.make_projection('.')
        with tempfile.TemporaryDirectory() as t:
            files=g.publish(t,d)
            self.assertTrue(all(Path(x).is_file() for x in files))
            self.assertIn('unavailable',json.loads(Path(files[0]).read_text())['git_status'])
    def test_escape_untrusted_branch_and_subject(self):
        d={'generated_at':'now','main_sha':None,'git_status':'available','pr_status':'available','workspace_context':'unknown','qualification':'observation', 'branches':[{'branch':'<script>alert(1)</script>','sha':'a'*40,'ahead':0,'behind':1,'integrated':False,'open_prs':[]}]}
        output=g.render(d)
        self.assertNotIn('<script>',output)
        self.assertIn('&lt;script&gt;',output)
    def test_atomically_publish_same_names(self):
        d={'generated_at':'now','main_sha':None,'git_status':'unavailable','pr_status':'unavailable','workspace_context':'unknown','qualification':'observation','branches':[]}
        with tempfile.TemporaryDirectory() as t:
            g.publish(t,d); g.publish(t,d)
            self.assertFalse(list(Path(t).glob('*.tmp')))
    def test_workspace_context_is_unknown(self):
        with patch.object(g,'branch_snapshot',return_value=('a'*40,[])),patch.object(g,'github_prs',return_value=([],'unavailable')):
            d=g.make_projection('.')
        self.assertIn('not reported',d['workspace_context'])

if __name__=='__main__':unittest.main()
