# Controller portability working-session terminal evidence

Evidence ID: SAGE-K3-GOVERNANCE-20260726-001
Collection date: 2026-07-26
Local timezone: America/Chicago
Operator: Don Buddenbaum

This artifact preserves the material terminal observations from the working
session. Long Git fast-forward file lists, dependency download progress, and
other unrelated output were trimmed. No credentials, private keys, kubeconfig
content, or secret values are included.

## EV-001 — Initial Mac mini bootstrap failure exposed controller coupling

Execution source: donb-mac-mini
Repository: donb4iu/Kalaxy3
Branch: main
Approximate local time: 2026-07-26T14:24:00-05:00

Command:

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab
rm -rf .venv .ansible
python3 --version
make install
make controller-preflight
make syntax
```

Observed material output:

```text
Python 3.13.5
Python 3.13.5 found; repository requires 3.12.4
make: *** [controller-bootstrap] Error 1
make: .venv/bin/python: No such file or directory
make: *** [controller-preflight] Error 1
make: .venv/bin/ansible-playbook: No such file or directory
make: *** [syntax] Error 1
```

Interpretation: the existing bootstrap correctly refused an unsupported system
Python, but it could not provision the repository-required Python itself.
Machine portability was therefore not yet complete.

## EV-002 — Clean iMac bootstrap and validation passed

Execution source: donbs-imac
Approximate local time: 2026-07-26T14:43:00-05:00 through
2026-07-26T14:46:00-05:00

Command:

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab
git -C ~/dvlp/Kalaxy3 diff --check &&
rm -rf .venv .ansible .tools .python .uv-cache &&
make install &&
make controller-preflight &&
make syntax
```

Observed material output:

```text
downloading uv 0.11.32 x86_64-apple-darwin
installing to .../infrastructure/k3s-homelab/.tools
everything's installed!
Installed Python 3.12.4
Using CPython 3.12.4
Installed 10 packages
 + ansible-core==2.18.7
 + jmespath==1.0.1
PASS uv 0.11.32
PASS Python 3.12.4
PASS ansible-core 2.18.7
PASS ansible.posix 1.6.2
PASS community.general 10.3.0
PASS kubernetes.core 5.1.0
Kalaxy3 controller preflight: PASS
playbook: playbooks/phases/phase-00-readiness.yml
playbook: playbooks/phases/phase-01-prerequisites.yml
playbook: playbooks/phases/phase-02-k3s.yml
playbook: playbooks/phases/phase-03-network-storage.yml
playbook: playbooks/phases/phase-04-ui.yml
playbook: playbooks/phases/phase-05-observability.yml
playbook: playbooks/phases/phase-06-minio.yml
```

Negative observation:

```text
The final clean run did not print:
skipping sha256 checksum verification
```

Interpretation: the iMac recreated and validated the pinned environment from
repository instructions after all disposable controller state was removed.

## EV-003 — Implementation commit was created and pushed

Execution source: donbs-imac
Local time: 2026-07-26T14:49:00-05:00

Observed material output:

```text
[main 5edd4e0] Provision repository-managed Python controllers
 4 files changed, 81 insertions(+), 11 deletions(-)
 create mode 100644 infrastructure/k3s-homelab/.uv-version
To github.com:donb4iu/Kalaxy3.git
   83d1038..5edd4e0  main -> main
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

Interpretation: the portability implementation entered the authoritative Git
repository before the second-machine proof.

## EV-004 — Clean Mac mini bootstrap reproduced the same environment

Execution source: donb-mac-mini
Local time: 2026-07-26T14:50:00-05:00 through
2026-07-26T14:51:00-05:00

Command:

```bash
cd ~/dvlp/Kalaxy3
git pull --ff-only origin main
cd infrastructure/k3s-homelab
printf 'System Python: '
python3 --version
rm -rf .venv .ansible .tools .python .uv-cache
make install &&
make controller-preflight &&
make syntax
```

Observed material output:

```text
System Python: Python 3.13.5
downloading uv 0.11.32 x86_64-apple-darwin
installing to .../infrastructure/k3s-homelab/.tools
everything's installed!
Installed Python 3.12.4
Using CPython 3.12.4
Installed 10 packages
 + ansible-core==2.18.7
 + jmespath==1.0.1
PASS uv 0.11.32
PASS Python 3.12.4
PASS ansible-core 2.18.7
PASS ansible.posix 1.6.2
PASS community.general 10.3.0
PASS kubernetes.core 5.1.0
Kalaxy3 controller preflight: PASS
playbook: playbooks/phases/phase-00-readiness.yml
playbook: playbooks/phases/phase-01-prerequisites.yml
playbook: playbooks/phases/phase-02-k3s.yml
playbook: playbooks/phases/phase-03-network-storage.yml
playbook: playbooks/phases/phase-04-ui.yml
playbook: playbooks/phases/phase-05-observability.yml
playbook: playbooks/phases/phase-06-minio.yml
```

Additional informational output:

```text
warning: /Users/dbuddenbaum/.local/bin is not on your PATH
```

Interpretation: the PATH warning did not affect Kalaxy3 because the Makefile
uses repository-local executable paths. The Mac mini began with system Python
3.13.5 but reproduced the same managed Python 3.12.4 and Ansible environment as
the iMac.

## EV-005 — Unrelated stale research file was removed

The Mac mini had one untracked, obsolete research PDF unrelated to the
implementation. It was deleted after the operator confirmed it no longer
belonged in the repository. Because it was never tracked, its removal produced
no Git commit and did not affect the portability evidence.
