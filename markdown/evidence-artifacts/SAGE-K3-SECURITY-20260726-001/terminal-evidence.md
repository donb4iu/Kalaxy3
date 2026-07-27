# Canonical Kalaxy3 controller-access working-session terminal evidence

Evidence ID: SAGE-K3-SECURITY-20260726-001
Work date: 2026-07-26
Local timezone: America/Chicago
Primary execution source: donbs-imac
Independent controller checks: donb-mac-mini
Operator: Don Buddenbaum

This artifact preserves the material terminal evidence from the controller
access working session. Repetitive dependency output and full public-key bodies
were omitted; approved public-key fingerprints and normalized comments are
preserved. No private keys, credentials, tokens, kubeconfig content, password
hashes, or secret values are included.

## EV-001 — Initial active-account and trust baseline

The pre-change inventory account model was:

```text
arm64-01 through arm64-05: ansible_user=pi
amd64-01 and amd64-02:    ansible_user=dbuddenbaum
```

An iMac baseline verified that all seven active inventory accounts accepted both
controller keys and passwordless sudo. A Mac mini baseline initially failed
closed before authentication because that checkout had stale repository SSH
host trust. After the authoritative `inventory/ssh_known_hosts` file was used,
the Mac mini reached all seven nodes with noninteractive SSH and sudo.

Preserved external artifact checksums:

```text
7cef60636b64e16f58aa5f010c27a8a78aab1b17bdf43a27e5f8076fe2ae50ae  kalaxy3-controller-access-baseline-20260726.txt
eea59ba6ea0cec301ed10324e30431564d97971e157d6e14d6ced0b3a6d704c5  kalaxy3-mac-mini-access-baseline-20260726.txt
0be2e191537bc3dd7c0c1d63b34c1e8655b33bb4ef0b5e4b9bf3fce5b30e63be  kalaxy3-mac-mini-access-baseline-corrected-20260726.txt
```

Approved controller fingerprints:

```text
SHA256:Yxc1nAYgB7jMlt1j3wKweIbtrNaQhl4a/lEKGM3x58M  ED25519  donb-mac-mini
SHA256:4+8+jbjhDiKgJr4JvLfZVc66TjNn84a7mWg9yk2Qkho  RSA-4096 donbs-imac
```

## EV-002 — Intel legacy administration path was directly observed

Read-only collection on `amd64-01` and `amd64-02` proved that each node had two
parallel root-capable paths.

Observed before state:

```text
account=pi
password_state=locked
authorized_key_count=1
authorized_key_fingerprint=SHA256:Yxc1nAYgB7jMlt1j3wKweIbtrNaQhl4a/lEKGM3x58M
sudoers=/etc/sudoers.d/90-kalaxy3-pi
sudo_rule=NOPASSWD ALL

account=dbuddenbaum
authorized_key_count=2
sudoers=/etc/sudoers.d/90-k3s-admin
sudo_rule=NOPASSWD ALL

canonical_sudoers=/etc/sudoers.d/90-kalaxy3-ansible-admin
canonical_sudoers_state=MISSING
```

Both legacy sudoers files parsed successfully, proving that this was active
configuration rather than dead documentation.

Artifact checksum:

```text
acccd6919b94e794b9c435a3aaa9a37d79638a27b191c80868773f83ed3773bc  kalaxy3-intel-legacy-access-state-20260726.txt
```

## EV-003 — Guardrail framework and controller identities were checkpointed

Before changing live access, the working branch passed repository controller,
source, K3s release, Helm, deployment-lock, syntax, strict SSH trust, and
seven-host access gates.

Material output:

```text
PASS uv 0.11.32 (darwin-amd64)
PASS Python 3.12.4
PASS ansible-core 2.18.7
PASS ansible.posix 1.6.2
PASS community.general 10.3.0
PASS kubernetes.core 5.1.0
PASS SSH host trust 7 nodes
Kalaxy3 SAGE source guardrails: PASS
Kalaxy3 SAGE K3s release guardrail: PASS
Kalaxy3 SAGE deployment guardrail: PASS
Kalaxy3 Helm lock reconciliation: PASS
PASS noninteractive Ansible authentication for 7 inventory hosts
Kalaxy3 SAGE bootstrap guardrails: PASS
```

The work was pushed in frequent checkpoints:

```text
92d7a8b Add SAGE infrastructure enforcement guardrails
2aa47b4 Record approved Kalaxy3 controller public keys
f68d27e Split SSH and privilege access preflights
4c82dd0 Add canonical controller access baseline
e77cb16 Fix access baseline check-mode validation
```

The final implementation lineage for this record is:

```text
e77cb1620e1f7b1231ebd162d9506d4123520c88
```

## EV-004 — SSH and privilege preflights were separated and validated

The original preflight inherited `ansible_become: true`, so it conflated SSH
authentication with privilege escalation. The replacement exposes three
scopes:

```text
make ssh-auth-preflight       # become explicitly false
make privilege-preflight      # noninteractive become and `id -u`
make ansible-access-preflight # both controls
```

Observed all-node results:

```text
arm64-01 through arm64-05: SSH pong; privilege UID 0
amd64-01 and amd64-02:     SSH pong; privilege UID 0
Kalaxy3 Ansible access preflight (ssh): PASS
Kalaxy3 Ansible access preflight (privilege): PASS
Kalaxy3 Ansible access preflight (all): PASS
Kalaxy3 SAGE bootstrap guardrails: PASS
Kalaxy3 SAGE recovery guardrails: PASS
```

The Ansible command module reported `CHANGED` while executing `id -u`; this was
module reporting and did not persist node state.

## EV-005 — Failed source and check-mode paths were corrected before rollout

The first source-update helper failed closed because it assumed a historical
copied public-key file still existed:

```text
Access-baseline source update failed:
Missing expected repository file:
infrastructure/k3s-homelab/playbooks/files/pi-admin-ed25519.pub
```

The corrected source helper treated the absent historical copy as an allowed
state and added the canonical playbook without contacting nodes.

The first `amd64-01 --check --diff` preview then exposed that a read-only
`getent passwd pi` command was skipped in check mode, leaving an undefined
registered value:

```text
fatal: list object has no element 5
```

Adding `check_mode: false` to the read-only `getent` and `id -nG` probes fixed
discovery. A second preview exposed a different check-mode condition: simulated
file deletion does not change a following real `stat`, so the post-removal
assertion failed. The assertion was restricted to real execution:

```yaml
when: not ansible_check_mode
```

One temporary correction helper also failed closed because it parsed Git's
porcelain leading status column incorrectly. A corrected helper validated that
only `access-baseline.yml` was modified.

The final read-only Intel canary preview completed:

```text
amd64-01: ok=10 changed=5 unreachable=0 failed=0 skipped=3
```

No node changes occurred during these preview failures or corrections.

## EV-006 — Real Intel canary converged and retired the legacy path

The real `amd64-01` canary ran from commit
`e77cb1620e1f7b1231ebd162d9506d4123520c88`.

Observed change:

```text
active_account=dbuddenbaum
approved_active_key_count=2
canonical_sudoers=/etc/sudoers.d/90-kalaxy3-ansible-admin
canonical_sudo_validation=PASS
legacy_90-k3s-admin=REMOVED
legacy_pi_password=LOCKED
legacy_pi_sudo_group=REMOVED
legacy_pi_authorized_keys=REMOVED
legacy_90-kalaxy3-pi=REMOVED

PLAY RECAP
amd64-01: ok=13 changed=6 unreachable=0 failed=0
```

Canary artifact checksum:

```text
17da31c7d496a850246490c94bd2ed0bc69bcc59381bfc0d7c51ee7462bc3dab  kalaxy3-access-baseline-amd64-01-canary-20260726.txt
```

Postvalidation proved exact fingerprints, sudoers ownership `root:root`, mode
`0440`, successful `visudo`, absent legacy paths, and idempotency:

```text
authorized_key_count=2
canonical_sudoers=root:root:440
legacy_90-k3s-admin=ABSENT
legacy_90-kalaxy3-pi=ABSENT
legacy_pi_sudo_group=ABSENT
legacy_pi_authorized_keys=ABSENT_OR_EMPTY

amd64-01: ok=12 changed=0 unreachable=0 failed=0
```

Postvalidation checksum:

```text
7c5f2421b1126c04b352c861b1c51fe1fa26599a591f02f802a10a4befb4563c  kalaxy3-access-baseline-amd64-01-postvalidation-20260726.txt
```

## EV-007 — Independent Mac mini validation passed on the Intel canary

The Mac mini updated to the same feature branch and connected directly with its
approved ED25519 key under strict repository-owned host trust.

Observed result:

```text
hostname=amd64-01
remote_user=dbuddenbaum
remote_uid=1000
sudo_uid=0
access_result=PASS
```

Artifact checksum:

```text
2311a70dc853436d5422f09adc4a8cf68f22e5e40dd9ac5c67c3af41cb83580c  kalaxy3-mac-mini-amd64-01-access-validation-20260726.txt
```

## EV-008 — ARM preview, canary, independent check, and idempotency passed

The read-only `arm64-01` preview proposed only the active `pi` account key
normalization and canonical sudoers installation. Intel-only retirement tasks
had no matching host.

Preview recap:

```text
arm64-01: ok=3 changed=2 unreachable=0 failed=0 skipped=1
```

Preview checksum:

```text
be586bea564444c9b3fe5287081bb4cce39e3df7babd64d2597720e39b070a1b  kalaxy3-access-baseline-arm64-01-preview-20260726.txt
```

Real canary recap:

```text
arm64-01: ok=4 changed=2 unreachable=0 failed=0
```

Canary checksum:

```text
f277d163ef657cee7767d17b25390b590435c1ade1ee5130e37be4a10b5eaf6f  kalaxy3-access-baseline-arm64-01-canary-20260726.txt
```

Postvalidation:

```text
inventory_account=pi
authorized_key_count=2
approved ED25519 fingerprint present
approved RSA-4096 fingerprint present
canonical_sudoers=root:root:440
visudo=PASS
sudo_uid=0
arm64-01 idempotency: changed=0 failed=0
```

Postvalidation checksum:

```text
069c1b566b1d446bad2138928e432eb4fb3cc1b47692bb2a819b5c02325e7dfd  kalaxy3-access-baseline-arm64-01-postvalidation-20260726.txt
```

The Mac mini then validated the representative ARM path:

```text
hostname=arm64-01
remote_user=pi
remote_uid=1000
sudo_uid=0
access_result=PASS
```

Mac mini ARM checksum:

```text
a559fb03b5d7f750ad848c4f419af2bda39cb3bfa15aea139211ea1b88aea409  kalaxy3-mac-mini-arm64-01-access-validation-20260726.txt
```

## EV-009 — Remaining five-node rollout passed

The playbook ran sequentially with `--forks 1` against:

```text
arm64-02
arm64-03
arm64-04
arm64-05
amd64-02
```

Observed recap:

```text
arm64-02: ok=4  changed=2 unreachable=0 failed=0
arm64-03: ok=4  changed=2 unreachable=0 failed=0
arm64-04: ok=4  changed=2 unreachable=0 failed=0
arm64-05: ok=4  changed=2 unreachable=0 failed=0
amd64-02: ok=13 changed=6 unreachable=0 failed=0
```

`amd64-02` also removed the legacy `pi` sudo group membership, SSH
authorization, and `90-kalaxy3-pi` file.

Rollout checksum:

```text
076c78d2e257892e87b55dd9a589ea5899fdb211ddd1ffcb44db386b61d17754  kalaxy3-access-baseline-remaining-nodes-20260726.txt
```

## EV-010 — Final seven-node state and idempotency passed

Final all-node SSH authentication:

```text
arm64-01 through arm64-05: pong
amd64-01 and amd64-02:     pong
Kalaxy3 Ansible access preflight (ssh): PASS
```

Final all-node privilege escalation:

```text
arm64-01 through arm64-05: UID 0
amd64-01 and amd64-02:     UID 0
Kalaxy3 Ansible access preflight (privilege): PASS
```

Every active inventory account had exactly two keys with these fingerprints:

```text
SHA256:Yxc1nAYgB7jMlt1j3wKweIbtrNaQhl4a/lEKGM3x58M  ED25519
SHA256:4+8+jbjhDiKgJr4JvLfZVc66TjNn84a7mWg9yk2Qkho  RSA-4096
```

Every node reported:

```text
canonical_sudoers=root:root:440:/etc/sudoers.d/90-kalaxy3-ansible-admin
visudo=parsed OK
legacy_90-k3s-admin=ABSENT
sudo_uid=0
```

Both Intel nodes reported:

```text
pi password state=LOCKED
legacy_90-kalaxy3-pi=ABSENT
legacy_pi_sudo_group=ABSENT
legacy_pi_authorized_keys=ABSENT_OR_EMPTY
```

Final idempotency recap:

```text
amd64-01: ok=12 changed=0 unreachable=0 failed=0
amd64-02: ok=12 changed=0 unreachable=0 failed=0
arm64-01: ok=4 changed=0 unreachable=0 failed=0
arm64-02: ok=4 changed=0 unreachable=0 failed=0
arm64-03: ok=4 changed=0 unreachable=0 failed=0
arm64-04: ok=4 changed=0 unreachable=0 failed=0
arm64-05: ok=4 changed=0 unreachable=0 failed=0
```

Final artifact checksum:

```text
46814bb44a0e7d1c6154c3d9085ec189b55ede19d42ea629991ae01bed3d85ae  kalaxy3-access-baseline-all-nodes-final-20260726.txt
```

## EV-011 — Repository source and temporary-helper integrity observations

Additional preserved checksums:

```text
2c05d9d4b98605a6cc18b13b37343b0d4276eba42c2d91566ae6495b7215d6d4  kalaxy3-access-source-audit-20260726.txt
87f9bf38204474857d586cc5fee03153e879493e4682d1d061eeece2547ed582  repository SSH known-hosts copy
988daba0568b1fcc5ec1c43b528c4bd746766ba9a19456607139f02d4e1dc559  kalaxy3-stage1-guardrails-review.patch
c069bc9f4c1e5f0114f7d335249eaf89e32ea93a95606ee4874d538f17f27faa  split-access-preflight helper
ddddf1d963ac4e32ac667e47c7ae8245c61def7d8f102d580053612f54e83129  canonical-access-baseline source helper
fc21fb6de04a82a01b5572f4ae084067eae3a85f4f55163ac8bb52a1818f214f  check-mode discovery correction helper
26e75671ac7489dd4d6d9650ee5e993ea005978a13781f6a82127d6ba6d5c4b4  check-mode assertion correction helper
```

The temporary helpers were delivery mechanisms, not repository sources of
truth. The accepted source of truth is the committed implementation under
`infrastructure/k3s-homelab`.
