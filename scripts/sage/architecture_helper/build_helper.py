#!/usr/bin/env python3
"""Evidence-bound read-only Architecture Helper MVP; no claims of runtime qualification."""
import argparse
import hashlib
import html
import json
from pathlib import Path

ROLES = ('responsible','consulted','informed','independent-referee','independent-reviewer','path-architecture-critic','task-narrator','objective-narrator')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_json(p):
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding='utf-8'))

def gather(episode, dispatch):
    state = read_json(episode/'objective-status.json')
    if not isinstance(state, dict) or state.get('record_type') != 'sage-breakglass-8020-functional-assessment':
        raise ValueError('missing or unexpected objective status; refuse fabricated dashboard')
    ev = [{'file':str(episode/'objective-status.json'),'sha256':sha(episode/'objective-status.json')}]
    decisions = {}
    for role in ROLES:
        p = episode/(role+'-response.json')
        result = read_json(p)
        if result is not None:
            rp = episode/(role+'-receipt.json')
            if not rp.is_file():
                raise ValueError('role response without invocation receipt: '+role)
            ev.extend([{'file':str(p),'sha256':sha(p)},{'file':str(rp),'sha256':sha(rp)}])
        decisions[role] = result
    existing = read_json(dispatch/'dispatch-result.json')
    for filename in ('dispatch-result.json','referee-decision.json','reviewer-decision.json','responsible-result.json'):
        p = dispatch/filename
        if p.is_file(): ev.append({'file':str(p),'sha256':sha(p)})
    # Locally supplied status booleans are claims, not authoritative proof.
    # This read-only projection deliberately has no verification authority.
    claimed = {key: state.get(key) for key in (
        'functionally_restored', 'governed_git_integration_verified',
        'protected_architecture_helper_verified')}
    return {'objective':state.get('objective','unspecified'), 'functional_delivery_verified':False,
            'status':'Not independently verified', 'reported_status_flags':claimed, 'role_responses':decisions,
            'dispatch':existing, 'objective_narration':state.get('narrator'), 'sources':ev,
            'note':'Local receipts and their hashes establish content correspondence only, not authenticity, Git qualification, Cloudflare authorization, or runtime delivery. Reported status flags are untrusted claims.'}

def render(data):
    esc=lambda v: html.escape(str(v), quote=True)
    def block(title, value):
        return '<section><h2>'+esc(title)+'</h2><pre>'+esc(json.dumps(value,indent=2,ensure_ascii=False))+'</pre></section>'
    roles=''.join(block(role.replace('-',' ').title(), data['role_responses'].get(role) or {'status':'not evidenced'}) for role in ROLES)
    evidence=''.join('<li><code>'+esc(e['sha256'][:20])+'</code> '+esc(e['file'])+'</li>' for e in data['sources'])
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kalaxy3 Architecture Helper — Evidence View</title><style>body{font:16px/1.55 system-ui;max-width:1050px;margin:30px auto;padding:0 18px;background:#f8fafc;color:#172033}section{background:white;border:1px solid #d8dee6;border-radius:10px;padding:18px;margin:16px 0}h1{font-size:1.8rem}pre{white-space:pre-wrap;overflow-wrap:anywhere}code{font-size:.8rem}li{margin-bottom:8px} .status{font-weight:700} .warning{color:#9a3412}</style></head><body><h1>Architecture Helper — objective evidence</h1><p class="status warning">'''+esc(data['status'])+''' — not an execution authorization</p><section><h2>Architect objective</h2><p>'''+esc(data['objective'])+'''</p></section>'''+block('Reported status flags (untrusted claims)',data['reported_status_flags'])+block('Functional narration (candidate, not established truth)',data['objective_narration'])+block('Latest engineering dispatch disposition',data['dispatch'])+'''<h2>Role perspectives (independent responses, unqualified)</h2>'''+roles+'''<section><h2>Evidence trace — SHA-256 of local receipts</h2><ul>'''+evidence+'''</ul><p>'''+esc(data['note'])+'''</p></section><section><h2>Architect choices</h2><p>Continue the existing approved objective; examine any material uncertainty; or redirect by an explicit Architect decision. These are descriptions, not executable controls and do not confer authority.</p></section></body></html>'''

def main():
    a=argparse.ArgumentParser();a.add_argument('--episode',type=Path,required=True);a.add_argument('--dispatch',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    x=a.parse_args(); data=gather(x.episode,x.dispatch);x.output.mkdir(parents=True,exist_ok=True)
    (x.output/'evidence.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    (x.output/'index.html').write_text(render(data),encoding='utf-8')
    print('ARCHITECTURE_HELPER_LOCAL='+str(x.output/'index.html'))
    print('FUNCTIONAL_DELIVERY_VERIFIED='+str(data['functional_delivery_verified']).lower())
    print('EVIDENCE_BINDINGS='+str(len(data['sources'])))
if __name__=='__main__': main()
