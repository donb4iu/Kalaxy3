# Kalaxy3 Intel Node `pi` Administrative Access Evidence

**Evidence date:** 2026-07-21  
**Cluster:** Kalaxy3  
**Nodes:** `amd64-01`, `amd64-02`  
**Repository area:** `infrastructure/k3s-homelab`  
**Purpose:** Preserve the Intel-node administrative-access design and rebuild
procedure.

## Executive Summary

The Raspberry Pi nodes receive their `pi` account, SSH authorization, and
administrative access from cloud-init when their boot media is flashed.

The Intel nodes are installed from Ubuntu ISO media. They therefore did not
automatically receive the same `pi` account and passwordless administration
configuration.

An Intel-specific Ansible playbook was added to:

1. Create the `pi` account on each Intel node.
2. Add `pi` to the `sudo` group.
3. Lock password-based login for the account.
4. Install the Mac mini controller's Ed25519 public key.
5. Grant `pi` passwordless sudo through a validated sudoers file.
6. Integrate the playbook into the Intel provisioning phase.

This produces the same operator workflow across Pi and Intel nodes:

```bash
ssh pi@<node-ip>
```

The implementation is intentionally Intel-specific because the Pi nodes
already receive equivalent configuration from cloud-init.

## Why This Was Necessary

The Intel nodes originally used the account:

```text
dbuddenbaum
```

The existing Pi administration workflow used:

```text
pi
```

Attempting to copy the Mac mini SSH key directly to `pi@192.168.2.61` and
`pi@192.168.2.62` failed because the `pi` account did not yet exist on the
Intel nodes.

The correct fix was not a manual `ssh-copy-id` operation. The missing account
and authorization were part of the Intel provisioning baseline and therefore
belonged in Ansible.

## Design Boundary

### Raspberry Pi nodes

The Pi nodes are configured through flash-time cloud-init. Their `pi` account
and SSH access should continue to be managed there.

### Intel nodes

The Intel nodes are installed from Ubuntu ISO media. Their Pi-compatible
administrative access is added after initial installation through Ansible.

### Why this was not added to shared prerequisites

Adding this configuration to the shared prerequisite playbook would
unnecessarily reconfigure the Pi nodes and duplicate cloud-init behavior.

The Intel-only provisioning sequence is:

```text
Ubuntu ISO installation
        |
        v
Initial SSH access as dbuddenbaum
        |
        v
intel-admin-access.yml
        |
        v
Shared prerequisites
        |
        v
K3s agent installation and join
```

## Repository Files

The implementation consists of:

```text
infrastructure/k3s-homelab/
├── playbooks/
│   ├── files/
│   │   └── pi-admin-ed25519.pub
│   ├── intel-admin-access.yml
│   └── phases/
│       └── phase-08-intel.yml
```

## Public Key Installation

The Mac mini controller's existing public key was copied into the repository:

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

mkdir -p playbooks/files

cp ~/.ssh/id_ed25519.pub   playbooks/files/pi-admin-ed25519.pub
```

The committed file is a public key and is safe to store in Git.

The corresponding private key must never be copied into the repository.

## Intel Administrative Access Playbook

File:

```text
playbooks/intel-admin-access.yml
```

Expected content:

```yaml
---
- name: Configure Pi-compatible administration on Intel nodes
  hosts: longhorn_nodes
  become: true
  gather_facts: false

  tasks:
    - name: Create the pi administrator account
      ansible.builtin.user:
        name: pi
        comment: Kalaxy3 administrator
        create_home: true
        shell: /bin/bash
        groups:
          - sudo
        append: true
        password_lock: true
        state: present

    - name: Create the pi SSH directory
      ansible.builtin.file:
        path: /home/pi/.ssh
        state: directory
        owner: pi
        group: pi
        mode: "0700"

    - name: Install the Kalaxy3 administrator public key
      ansible.builtin.copy:
        src: files/pi-admin-ed25519.pub
        dest: /home/pi/.ssh/authorized_keys
        owner: pi
        group: pi
        mode: "0600"

    - name: Configure passwordless sudo for pi
      ansible.builtin.copy:
        dest: /etc/sudoers.d/90-kalaxy3-pi
        content: "pi ALL=(ALL:ALL) NOPASSWD: ALL\n"
        owner: root
        group: root
        mode: "0440"
        validate: /usr/sbin/visudo -cf %s
```

## Intel Phase Integration

File:

```text
playbooks/phases/phase-08-intel.yml
```

Expected content:

```yaml
---
- import_playbook: ../intel-admin-access.yml
- import_playbook: ../prerequisites.yml
- import_playbook: ../k3s.yml
```

The administrative-access playbook runs first so the standard `pi` account
exists before the remaining Intel provisioning steps.

## Syntax Validation Evidence

The updated Intel phase was validated with:

```bash
ansible-playbook   -i inventory/hosts.yml   playbooks/phases/phase-08-intel.yml   --syntax-check
```

Observed result:

```text
playbook: playbooks/phases/phase-08-intel.yml
```

## Provisioning Evidence

The Intel-only access playbook was run with:

```bash
ansible-playbook   -i inventory/hosts.yml   playbooks/intel-admin-access.yml   --ask-become-pass
```

Observed result:

```text
PLAY [Configure Pi-compatible administration on Intel nodes]

TASK [Create the pi administrator account]
changed: [amd64-01]
changed: [amd64-02]

TASK [Create the pi SSH directory]
changed: [amd64-01]
changed: [amd64-02]

TASK [Install the Kalaxy3 administrator public key]
changed: [amd64-01]
changed: [amd64-02]

TASK [Configure passwordless sudo for pi]
changed: [amd64-01]
changed: [amd64-02]

PLAY RECAP
amd64-01 : ok=4 changed=4 unreachable=0 failed=0
amd64-02 : ok=4 changed=4 unreachable=0 failed=0
```

This proves both Intel nodes received the complete administrative-access
configuration.

## Functional Verification Evidence

Password authentication was explicitly disabled during the test:

```bash
ssh -o PasswordAuthentication=no   pi@192.168.2.61   'hostname; sudo -n true && echo sudo-ready'

ssh -o PasswordAuthentication=no   pi@192.168.2.62   'hostname; sudo -n true && echo sudo-ready'
```

Observed result:

```text
amd64-01
sudo-ready
amd64-02
sudo-ready
```

This verifies:

- The `pi` account exists on both nodes.
- SSH public-key authentication succeeds.
- Password authentication is not required.
- Passwordless sudo succeeds.
- The correct nodes were reached.

## Rebuild Procedure

Use the following procedure when rebuilding an Intel Kalaxy3 node.

### 1. Install Ubuntu

Install the supported Ubuntu release from ISO media.

Create the initial account used by Ansible and establish network access.

For the current Intel nodes:

```text
amd64-01: 192.168.2.61
amd64-02: 192.168.2.62
```

### 2. Confirm initial Ansible access

The initial inventory connection may continue to use:

```yaml
ansible_user: dbuddenbaum
```

Test connectivity without privilege escalation:

```bash
ansible   -i inventory/hosts.yml   amd64-02   -m ping   -e ansible_become=false
```

### 3. Confirm the committed public key

```bash
test -f playbooks/files/pi-admin-ed25519.pub

ssh-keygen   -lf playbooks/files/pi-admin-ed25519.pub
```

### 4. Run Intel administrative-access provisioning

```bash
ansible-playbook   -i inventory/hosts.yml   playbooks/intel-admin-access.yml   --ask-become-pass
```

### 5. Verify key-only login

```bash
ssh -o PasswordAuthentication=no   pi@192.168.2.61   'hostname; id'
```

### 6. Verify passwordless sudo

```bash
ssh -o PasswordAuthentication=no   pi@192.168.2.61   'sudo -n whoami'
```

Expected:

```text
root
```

### 7. Continue the complete Intel phase

```bash
ansible-playbook   -i inventory/hosts.yml   playbooks/phases/phase-08-intel.yml   --ask-become-pass   --vault-id kalaxy3@prompt
```

## Idempotency

The playbook uses idempotent Ansible modules.

Run it a second time:

```bash
ansible-playbook   -i inventory/hosts.yml   playbooks/intel-admin-access.yml   --ask-become-pass
```

The expected steady-state result is:

```text
amd64-01 : ok=4 changed=0 unreachable=0 failed=0
amd64-02 : ok=4 changed=0 unreachable=0 failed=0
```

The first-run evidence is captured above. A second-run idempotency result had
not yet been recorded when this evidence page was created.

## Security Model

### Locked password

The Ansible user task specifies:

```yaml
password_lock: true
```

This prevents password-based login to the `pi` account while permitting SSH
public-key authentication.

### Passwordless sudo

The sudoers entry is:

```text
pi ALL=(ALL:ALL) NOPASSWD: ALL
```

Anyone with the corresponding private SSH key can obtain root access on the
Intel nodes.

The Mac mini controller and its private key must therefore remain protected.

### Public key in Git

This file is safe to commit:

```text
playbooks/files/pi-admin-ed25519.pub
```

Files that must never be committed include:

```text
~/.ssh/id_ed25519
```

or any other private-key file.

### Sudoers validation

The playbook validates the sudoers file before installing it:

```yaml
validate: /usr/sbin/visudo -cf %s
```

This prevents an invalid sudoers file from being written.

## Troubleshooting

### `Permission denied` for `pi`

Check that the account exists:

```bash
ansible   -i inventory/hosts.yml   amd64-01   --become   --ask-become-pass   -m command   -a 'id pi'
```

Check permissions:

```bash
ansible   -i inventory/hosts.yml   amd64-01   --become   --ask-become-pass   -m shell   -a '
    stat -c "%U %G %a %n" /home/pi/.ssh
    stat -c "%U %G %a %n" /home/pi/.ssh/authorized_keys
  '
```

Expected:

```text
pi pi 700 /home/pi/.ssh
pi pi 600 /home/pi/.ssh/authorized_keys
```

### Public-key mismatch

Compare fingerprints:

```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub
ssh-keygen -lf playbooks/files/pi-admin-ed25519.pub
```

The fingerprints should match unless key rotation was intentional.

### Passwordless sudo fails

Validate the installed file:

```bash
ssh pi@192.168.2.61   'sudo visudo -cf /etc/sudoers.d/90-kalaxy3-pi'
```

Expected:

```text
/etc/sudoers.d/90-kalaxy3-pi: parsed OK
```

Then test:

```bash
ssh pi@192.168.2.61   'sudo -n whoami'
```

Expected:

```text
root
```

### The playbook asks for a become password

The current inventory connects as `dbuddenbaum`. The initial sudo password is
therefore still required when Ansible provisions or repairs the `pi` account.

Changing `ansible_user` to `pi` is a separate inventory decision and should be
made only after the `pi` configuration has been verified on every Intel node.

## Evidence Checklist

- [x] Intel-only administrative-access design selected.
- [x] Mac mini public key copied to `playbooks/files`.
- [x] Intel administrative-access playbook created.
- [x] Intel provisioning phase syntax validated.
- [x] `pi` account created on `amd64-01`.
- [x] `pi` account created on `amd64-02`.
- [x] Key-only SSH verified on `amd64-01`.
- [x] Key-only SSH verified on `amd64-02`.
- [x] Passwordless sudo verified on `amd64-01`.
- [x] Passwordless sudo verified on `amd64-02`.
- [ ] Second-run idempotency evidence recorded.
- [ ] Repository changes committed and pushed.

## Git Review and Commit

Review the working tree:

```bash
cd ~/dvlp/Kalaxy3

git status --short
git diff --check
git diff
```

Stage the implementation and evidence:

```bash
git add   infrastructure/k3s-homelab/playbooks/files/pi-admin-ed25519.pub   infrastructure/k3s-homelab/playbooks/intel-admin-access.yml   infrastructure/k3s-homelab/playbooks/phases/phase-08-intel.yml   markdown/installation/kalaxy3-intel-pi-admin-access-evidence.md
```

Suggested commit:

```bash
git commit -m   "Add Pi-compatible administration to Intel nodes"
```

Push after reconciling with the remote branch:

```bash
git pull --rebase origin main
git push origin main
git status
```
