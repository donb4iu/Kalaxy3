#!/usr/bin/env python3
"""Git-first, read-only multi-user dashboard projection. No evidence/execution gating."""
import argparse
import datetime as dt
import html
import json
import os
import subprocess
import urllib.request
from pathlib import Path


def run(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def branch_snapshot(repo):
    """Published refs as observed by this clone; no local workstation inference."""
    run(repo, 'fetch', '--prune', 'origin', '+refs/heads/*:refs/remotes/origin/*')
    head = run(repo, 'rev-parse', 'refs/remotes/origin/main')
    raw = run(repo, 'for-each-ref', '--format=%(refname:short)\t%(objectname)\t%(committerdate:iso8601-strict)\t%(subject)', 'refs/remotes/origin/')
    result = []
    for line in raw.splitlines():
        fields = line.split('\t', 3)
        if len(fields) != 4: continue
        ref, sha, observed, subject = fields
        if ref == 'origin/HEAD': continue
        branch = ref.removeprefix('origin/')
        if branch == 'HEAD': continue
        counts = run(repo, 'rev-list', '--left-right', '--count', f'{head}...{sha}').split()
        if len(counts) != 2: continue
        behind, ahead = map(int, counts)
        result.append(dict(branch=branch, sha=sha, commit_time=observed, subject=subject,
                           ahead=ahead, behind=behind, integrated=(branch == 'main')))
    return head, sorted(result, key=lambda b:(b['branch'] != 'main', b['branch']))


def github_prs(repo_slug, token):
    if not repo_slug or not token:
        return [], 'PR details unavailable (GitHub API credentials or repository identity not provided)'
    prs = []
    try:
        for page in range(1, 11):
            url = f'https://api.github.com/repos/{repo_slug}/pulls?state=open&per_page=100&page={page}'
            req = urllib.request.Request(url, headers={'Authorization':f'Bearer {token}', 'Accept':'application/vnd.github+json', 'User-Agent':'kalaxy3-architect-observability'})
            with urllib.request.urlopen(req,timeout=20) as response:
                items = json.load(response)
            for item in items:
                prs.append({'number':item['number'], 'title':item['title'], 'branch':item['head']['ref'],
                            'base':item['base']['ref'], 'url':item['html_url'], 'draft':bool(item['draft']),
                            'updated_at':item['updated_at']})
            if len(items) < 100: return prs, 'available'
        return prs, 'partial: GitHub pagination limit reached'
    except Exception as ex:
        return prs, 'PR details unavailable: ' + type(ex).__name__


def make_projection(repo, repo_slug=None, token=None, generated_at=None):
    now = generated_at or dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        main_sha, branches = branch_snapshot(repo)
        git_state = 'available'
    except (OSError, subprocess.CalledProcessError, ValueError) as ex:
        main_sha, branches = None, []
        git_state = f'unavailable: {type(ex).__name__}'
    prs, pr_state = github_prs(repo_slug, token)
    pr_by_branch = {}
    for pr in prs: pr_by_branch.setdefault(pr['branch'], []).append(pr['number'])
    for branch in branches: branch['open_prs'] = pr_by_branch.get(branch['branch'], [])
    return {'schema_version':'1.0','record_type':'architect-shared-git-observation',
            'generated_at':now, 'source':'remote Git refs and optional GitHub pull requests',
            'repository':repo_slug or 'unspecified', 'main_sha':main_sha,
            'git_status':git_state, 'pr_status':pr_state, 'branches':branches, 'open_pull_requests':prs,
            'workspace_context':'not reported; local-only branches and active workstation branch are unknown',
            'qualification':'Observations only; commit or merge is not runtime proof; absence of observations is not a gate'}


def render(data):
    e=lambda value:html.escape(str(value),quote=True)
    rows=[]
    for b in data['branches']:
        prs=', '.join('#'+str(n) for n in b['open_prs']) or '—'
        label='Integrated baseline' if b['integrated'] else 'Published work in progress'
        rows.append(f'<tr><td>{e(b["branch"])}</td><td>{e(label)}</td><td><code>{e(b["sha"][:12])}</code></td><td>{b["ahead"]} ahead / {b["behind"]} behind</td><td>{e(prs)}</td></tr>')
    if not rows: rows=['<tr><td colspan="5">Git observations unavailable; dashboard remains available</td></tr>']
    return ('<section class="ae-git" aria-label="Shared development activity"><h2>What is integrated and in progress?</h2>'
            f'<p>Shared repository observed: {e(data["generated_at"])}. Current integrated baseline: {e(data["main_sha"] or "Unknown")}.</p>'
            f'<p>Repository: {e(data["git_status"])}. Pull requests: {e(data["pr_status"])}.</p>'
            '<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%"><thead><tr><th>Branch</th><th>Position</th><th>Commit</th><th>Divergence</th><th>Open PR</th></tr></thead><tbody>'
            +''.join(rows)+'</tbody></table></div>'
            f'<p>{e(data["workspace_context"])}</p><p>{e(data["qualification"])}</p></section>')


def publish(out, projection):
    """Atomic replacement of disposable HTML/JSON assets in an explicitly supplied shared static root."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Architect Enabler — development activity</title><style>body{font:16px/1.5 system-ui;max-width:1080px;margin:auto;padding:24px;color:#18283a}td,th{text-align:left;padding:10px;border-bottom:1px solid #ccc}code{word-break:break-all}</style></head><body>'+render(projection)+'</body></html>'
    for name, text in [('git-observations.json',json.dumps(projection,indent=2,ensure_ascii=False)+'\n'),('git-activity.html',page)]:
        destination=out/name; tmp=out/(name+'.tmp')
        tmp.write_text(text,encoding='utf-8');os.replace(tmp,destination)
    return [str(out/'git-observations.json'),str(out/'git-activity.html')]


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--repository',default=os.getenv('GITHUB_REPOSITORY'));p.add_argument('--no-github-api',action='store_true')
    args=p.parse_args();token=None if args.no_github_api else os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
    data=make_projection(args.repo,args.repository,token)
    print(json.dumps({'status':'PROJECTED_NOT_GOVERNED','assets':publish(args.out,data),'main_sha':data['main_sha'],'branch_count':len(data['branches']),'git_status':data['git_status'],'pr_status':data['pr_status']},indent=2))

if __name__=='__main__':main()
