#!/usr/bin/env python3
"""Read-only projection artifact checker. Missing Git observations are data, not a SAGE gate."""
import hashlib, json, pathlib, sys

def verify(root):
    root=pathlib.Path(root)
    html=root/'git-activity.html'
    observation=root/'git-observations.json'
    if not html.is_file() or not observation.is_file():
        raise ValueError('publication assets missing (publication operation cannot proceed)')
    data=json.loads(observation.read_text(encoding='utf-8'))
    if data.get('record_type')!='architect-shared-git-observation':
        raise ValueError('unexpected observation type')
    if data.get('schema_version')!='1.0' or not isinstance(data.get('branches'),list):
        raise ValueError('unexpected observation structure')
    markup=html.read_text(encoding='utf-8')
    if '<html' not in markup or 'Shared development activity' not in markup:
        raise ValueError('unexpected static HTML')
    return {'status':'publication-input-validated','projection_sha256':hashlib.sha256(observation.read_bytes()).hexdigest(),'html_sha256':hashlib.sha256(html.read_bytes()).hexdigest(),'main_sha':data.get('main_sha'),'git_status':data.get('git_status'),'branch_count':len(data['branches'])}

if __name__=='__main__':
    try: print(json.dumps(verify(sys.argv[1]),sort_keys=True))
    except (IndexError,ValueError,OSError) as exc: raise SystemExit('publication input invalid: '+str(exc))
