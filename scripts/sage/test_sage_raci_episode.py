import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sage_raci_episode as mod
class Tests(unittest.TestCase):
 def fixture(self,root):
  root.mkdir(exist_ok=True)
  parts={}
  for name in mod.ROLES:
   fn=name+'-receipt.json'; (root/fn).write_text('{"role":"'+name+'"}')
   parts[name]={'invoked':True,'receipt_file':fn}
  (root/'result.json').write_text(json.dumps({'case':'historical','deterministic_oracle':{'status':'pass','runtime_command_executed':False},'role_qualification':'pass','participants':parts}))
 def test_missing_receipt_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t); self.fixture(p);(p/'responsible-receipt.json').unlink()
   with self.assertRaises(ValueError):mod.validate_prior(p)
 def test_unearned_execution_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.fixture(p);v=mod.load(p/'result.json');v['deterministic_oracle']['runtime_command_executed']=True;(p/'result.json').write_text(json.dumps(v))
   with self.assertRaises(ValueError):mod.validate_prior(p)
 def test_full_receipt_bound_handoff(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.fixture(p/'episode');out=p/'out'
   fake=lambda **kw: ({'findings':[],'limitations':[],'recommendation':'pending'} if 'Consulted' in kw['system_instruction'] else {'confirmed':[],'unproven':['runtime'],'communication':'pending'}, {'provider':'test','role':'isolated'})
   with patch.object(mod,'invoke_ollama_json',side_effect=fake) as inv: result=mod.run(p/'episode',out,'endpoint','model')
   self.assertEqual(inv.call_count,2);self.assertEqual(len(result['participants']),8)
   self.assertEqual(result['governed_execution'],'not-proven')
   self.assertEqual(mod.load(out/'evidence-observatory.json')['checked_receipts'],8)
if __name__=='__main__':unittest.main()
