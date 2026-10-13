#!/usr/bin/env python3
"""Receipt-grounded role completion for a historical replay; no execution authority."""
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path
from llm_role_invocation import invoke_ollama_json

ROLES=('responsible','referee','reviewer','path-architecture-critic','task-narrator','objective-narrator')

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise ValueError(f'not a JSON object: {path}')
    return value

def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    path.chmod(0o600)

def validate_prior(episode):
    result_path=episode/'result.json'
    result=load(result_path)
    if result.get('deterministic_oracle',{}).get('status')!='pass' or result.get('role_qualification')!='pass':
        raise ValueError('historical decision replay not qualified')
    participants=result.get('participants') or {}
    receipts={}
    for role in ROLES:
        item=participants.get(role)
        if not isinstance(item,dict) or item.get('invoked') is not True: raise ValueError(f'missing invoked role {role}')
        receipt_name=item.get('receipt_file')
        if not isinstance(receipt_name,str) or Path(receipt_name).name!=receipt_name: raise ValueError('unsafe receipt name')
        path=episode/receipt_name
        if not path.is_file(): raise ValueError(f'missing receipt {role}')
        receipt=load(path)
        if not receipt: raise ValueError(f'empty receipt {role}')
        receipts[role]={'path':str(path),'sha256':digest(path),'level':'invoked-unqualified'}
    if result.get('deterministic_oracle',{}).get('runtime_command_executed') is True:
        raise ValueError('unexpected execution claim in historical decision replay')
    return result, {'path':str(result_path),'sha256':digest(result_path)},receipts

def run(episode,output,endpoint,model):
    result,source,participants=validate_prior(episode)
    envelope={'historical_case':result['case'],'historical_replay_receipt':source,
              'decision_oracle_status':result['deterministic_oracle']['status'],
              'runtime_execution':'not performed','role_receipts':participants,
              'current_objective':'Break-glass restoration of SAGE RACI and observability, then governed functional execution',
              'authority':'no new approval or execution authorization conferred'}
    put(output/'participation-input.json',envelope)
    if not endpoint or not model: raise ValueError('qualified inference endpoint and model required')
    consultations=[]
    for role,instruction in [
        ('consulted','You are a fresh isolated Consulted specialist. Identify pertinent risks, missing information, and alternatives for the historical SAGE recovery, grounded solely in the supplied evidence. Return JSON with keys findings (array of strings), limitations (array of strings), and recommendation (string). Do not claim execution or authority.'),
        ('informed','You are a fresh isolated Informed participant. Summarize confirmed progress, unproven work, and next objective-level action for stakeholders using only supplied evidence. Return JSON with keys confirmed (array of strings), unproven (array of strings), and communication (string). Never assert execution success.')]:
        response,receipt=invoke_ollama_json(envelope=envelope,endpoint=endpoint,model=model,
            think='low',num_ctx=32768,num_predict=1600,temperature=0,response_format='json',system_instruction=instruction)
        if not isinstance(response,dict): raise ValueError(f'{role} invalid response')
        expected=('findings','limitations','recommendation') if role=='consulted' else ('confirmed','unproven','communication')
        if not all(k in response for k in expected): raise ValueError(f'{role} incomplete response')
        put(output/(role+'-response.json'),response)
        put(output/(role+'-receipt.json'),receipt)
        participants[role]={'path':str(output/(role+'-receipt.json')),'sha256':digest(output/(role+'-receipt.json')),'level':'invoked-unqualified'}
        consultations.append(role)
    telemetry={'record_type':'sage-participation-telemetry-projection','source':source,
               'participants':participants,'not_equivalent_to':'independent functional qualification',
               'roles_invoked':list(participants),'correction_loop_completed':False}
    put(output/'participation-telemetry.json',telemetry)
    observatory={'record_type':'sage-evidence-observatory-assessment','source':source,
                 'checked_receipts':len(participants),'participation_sha256':digest(output/'participation-telemetry.json'),
                 'historical_decision':'pass','narration':'prior independently qualified as pass',
                 'runtime_execution':'not-performed','evidence_integrity':'verified-for-this-episode',
                 'limits':['Not a source-backed functional replay','No canonical governed execution receipt','No verified Accountable-authority binding']}
    put(output/'evidence-observatory.json',observatory)
    report={'record_type':'sage-raci-episode-qualification','case':result['case'],'source':source,
            'participants':participants,'consulted_informed':consultations,
            'participation_telemetry':'recorded','evidence_observatory':'bounded-evidence-assessment',
            'architect_accountable_authority':'not-verified-from-this-episode',
            'source_implementation_replay':'not-performed','governed_execution':'not-proven',
            'status':'observed-participation-only'}
    put(output/'result.json',report)
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--episode',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    try:
        value=run(a.episode.resolve(),a.output.resolve(),os.environ.get('SAGE_LLM_ROLE_ENDPOINT',''),os.environ.get('SAGE_LLM_ROLE_MODEL',''))
    except Exception as exc:
        put(a.output/'blocker.json',{'status':'blocked','reason':str(exc),'execution_authorized':False})
        raise SystemExit(f'RACI_EPISODE_BLOCKED={exc}')
    print('RACI_PARTICIPATION_RECEIPTS='+str(len(value['participants'])))
    print('CONSULTED=INVOKED; INFORMED=INVOKED')
    print('PARTICIPATION_TELEMETRY=WRITTEN')
    print('EVIDENCE_OBSERVATORY=BOUNDED_ASSESSMENT')
    print('ACCOUNTABLE_AUTHORITY=NOT_VERIFIED')
    print('SOURCE_FUNCTIONAL_REPLAY=NOT_PERFORMED')
    print('GOVERNED_EXECUTION=NOT_YET_PROVEN')
    print('REPORT='+str(a.output.resolve()/'result.json'))
if __name__=='__main__':main()
