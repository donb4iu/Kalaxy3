"""Evidence-only participation observatory for break-glass RACI recovery.
Never turns source references, proposed work, or test runs into role participation.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROLES = ('Architect / Accountable','Responsible','Consulted','Informed','Independent Referee',
         'Independent Reviewer','Task Narrator','Objective Narrator','Path / Architecture Critic',
         'Participation Telemetry','Evidence Observatory')
# Existing receipts show invocation, not correctness or permission to execute.
SOURCES = {
    'Responsible': ('responsible-receipt.json','responsible-result.json'),
    'Independent Referee': ('referee-decision.json',),
    'Independent Reviewer': ('reviewer-decision.json',),
}

def _load(p):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):
        return None

def _hash(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def observe(directory: Path):
    directory=directory.resolve()
    facts={}
    for role in ROLES:
        required=SOURCES.get(role,())
        entries=[]
        for name in required:
            path=directory/name
            if path.is_file() and isinstance(_load(path),dict):
                entries.append({'path':str(path),'sha256':_hash(path)})
        invoked= bool(required) and len(entries)==len(required)
        facts[role]={'participation':'receipt-present-unqualified' if invoked else 'not-evidenced',
                     'receipts':entries}
    result=_load(directory/'dispatch-result.json') or {}
    authority=result.get('authority',{})
    qualified=authority.get('execution_authorized') is True and authority.get('contribution_qualified') is True
    # Cannot use an untrusted dispatcher claim as proof of execution; report existence only.
    return {'record_type':'sage-participation-evidence-observation','schema_version':'1.0',
            'assessment':'file-byte-presence-only; no authority or causal validation',
            'source_directory':str(directory),'roles':facts,
            'functional_outcome_verified':False,'governed_execution_verified':False,
            'unproven_roles':[r for r,v in facts.items() if v['participation']=='not-evidenced'],
            'claimed_authority_in_untrusted_result':qualified,
            'next_boundary':'historical causal episode with independent validated oracle and governed execution receipts'}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--episode',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    result=observe(a.episode)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('SAGE_PARTICIPATION_OBSERVATION=WRITTEN')
    for role,v in result['roles'].items(): print(f"{role}: {v['participation']}")
    print('GOVERNED_EXECUTION=NOT_YET_PROVEN')
    print('RECEIPT='+str(a.output))
if __name__=='__main__': main()
