# K3s API High Availability with kube-vip

**Project:** Kalaxy3
**Cluster:** Kalaxy3 K3s homelab
**Implemented:** July 16, 2026
**Status:** kube-vip deployed and API VIP verified
**Publication:** Safe to commit and push

## Purpose

Kalaxy3 already had a highly available embedded-etcd control plane:

| Node | Address | Role |
|---|---|---|
| `arm64-01` | `192.168.2.51` | `control-plane,etcd` |
| `arm64-02` | `192.168.2.52` | `control-plane,etcd` |
| `arm64-03` | `192.168.2.53` | `control-plane,etcd` |
| `arm64-04` | `192.168.2.54` | Agent |
| `arm64-05` | `192.168.2.55` | Agent |

The cluster could tolerate the loss of one control-plane member, but the
administration kubeconfig and K3s registration configuration used only:

```text
https://192.168.2.51:6443
```

That made `arm64-01` a single access-path dependency. The cluster could remain
healthy after losing `arm64-01`, but clients using that kubeconfig would not
automatically reconnect through `arm64-02` or `arm64-03`.

kube-vip was added to provide a floating Kubernetes API endpoint:

```text
https://192.168.2.50:6443
```

One control-plane node advertises the VIP at a time. If that node becomes
unavailable, kube-vip leader election allows another control-plane member to
advertise the same address.

## Network Allocation

```text
192.168.2.20-192.168.2.49   MetalLB service address pool
192.168.2.50                Kubernetes API virtual IP
192.168.2.51-192.168.2.53   K3s control-plane and etcd nodes
192.168.2.54-192.168.2.55   K3s agent nodes
```

kube-vip is configured only for the control-plane API VIP. It does not manage
Kubernetes `LoadBalancer` services. MetalLB remains responsible for those
addresses.

## Predeployment Validation

The control-plane LAN interface was confirmed as:

```text
eth0
```

Duplicate-address detection was performed from `arm64-01`:

```bash
sudo arping \
  -D \
  -I eth0 \
  -c 4 \
  192.168.2.50
```

Captured result:

```text
Sent 4 probes (4 broadcast(s))
Received 0 response(s)
PASS: 192.168.2.50 appears unused.
```

The VIP must also remain outside the router DHCP allocation range.

## Original Repository Configuration

The repository originally defined:

```yaml
k3s_api_endpoint: 192.168.2.51
```

That one variable controlled:

1. The K3s API certificate SAN.
2. Remaining control-plane server registration.
3. Agent registration.
4. The exported kubeconfig endpoint.

The server template originally contained:

```yaml
tls-san:
  - "{{ k3s_api_endpoint }}"
```

## Repository Changes

### Inventory variables

The following variables were added to
`infrastructure/k3s-homelab/inventory/group_vars/all.yml`:

```yaml
k3s_api_endpoint: 192.168.2.51
k3s_api_vip: 192.168.2.50
k3s_api_interface: eth0

k3s_tls_sans:
  - 192.168.2.51
  - 192.168.2.50
```

The endpoint remained `.51` during certificate preparation. The VIP was added
as an additional certificate SAN before kube-vip advertised it.

### K3s server template

The original block in `templates/k3s-server-config.yml.j2`:

```yaml
tls-san:
  - "{{ k3s_api_endpoint }}"
```

was replaced with:

```yaml
tls-san:
{% for san in k3s_tls_sans %}
  - "{{ san }}"
{% endfor %}
```

This rendered both addresses into every K3s API certificate:

```yaml
tls-san:
  - "192.168.2.51"
  - "192.168.2.50"
```

### Rolling restart support

The server configuration template tasks notify a handler:

```yaml
notify: Restart K3s
```

Each server play contains a handler at the same indentation level as `tasks:`:

```yaml
handlers:
  - name: Restart K3s
    ansible.builtin.systemd:
      name: k3s
      state: restarted
```

A handler flush was added inside the `tasks:` list after the install task and
before the API readiness check:

```yaml
- name: Apply pending K3s restart
  ansible.builtin.meta: flush_handlers
```

The server plays retain:

```yaml
serial: 1
```

This ensures that only one embedded-etcd/control-plane member restarts at a
time.

The remaining-server readiness check validates the local API before continuing:

```yaml
- name: Wait for the Kubernetes API
  ansible.builtin.command:
    cmd: k3s kubectl get --raw=/readyz
  register: server_ready
  retries: 30
  delay: 5
  until:
    - server_ready.rc == 0
    - server_ready.stdout == "ok"
  changed_when: false
```

## Certificate Rollout

The server-only rollout was performed while `.51` remained the active endpoint:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/k3s.yml \
  --vault-id kalaxy3@prompt \
  --limit k3s_servers
```

The play completed successfully for all three control-plane nodes:

```text
arm64-01   unreachable=0   failed=0
arm64-02   unreachable=0   failed=0
arm64-03   unreachable=0   failed=0
```

All five nodes returned `Ready`, and all deployed workloads remained healthy.

The live configuration on every control-plane node showed:

```yaml
tls-san:
  - "192.168.2.51"
  - "192.168.2.50"
```

The certificates served by `.51`, `.52`, and `.53` included:

```text
IP Address:192.168.2.50
IP Address:192.168.2.51
IP Address:192.168.2.52
IP Address:192.168.2.53
```

## kube-vip Manifest Generation

Docker was not installed on the administration Mac. The kube-vip DaemonSet was
therefore generated using the containerd runtime bundled with K3s on
`arm64-01`.

The kube-vip image was pulled on `arm64-01`:

```bash
KVVERSION="v1.2.1"

ssh pi@192.168.2.51 \
  "sudo k3s ctr images pull \
  ghcr.io/kube-vip/kube-vip:${KVVERSION}"
```

The manifest was generated remotely and saved in the repository:

```bash
VIP="192.168.2.50"
INTERFACE="eth0"

ssh pi@192.168.2.51 \
  "sudo k3s ctr run \
    --rm \
    --net-host \
    ghcr.io/kube-vip/kube-vip:${KVVERSION} \
    kube-vip-manifest \
    /kube-vip manifest daemonset \
      --interface ${INTERFACE} \
      --address ${VIP} \
      --inCluster \
      --taint \
      --controlplane \
      --arp \
      --leaderElection" \
  > manifests/kube-vip/kube-vip-daemonset.yaml
```

Important options:

| Option | Purpose |
|---|---|
| `--interface eth0` | Advertise the VIP on the control-plane LAN interface |
| `--address 192.168.2.50` | Define the Kubernetes API VIP |
| `--inCluster` | Use in-cluster Kubernetes authentication |
| `--taint` | Permit scheduling on tainted control-plane nodes |
| `--controlplane` | Enable control-plane VIP management |
| `--arp` | Advertise the VIP with layer-2 ARP |
| `--leaderElection` | Elect one active VIP owner |

The `--services` option was intentionally omitted. This prevents kube-vip from
competing with MetalLB.

The generated manifest used:

```text
ghcr.io/kube-vip/kube-vip:v1.2.1
```

## Deployment

The kube-vip RBAC and DaemonSet manifests were applied:

```bash
kubectl apply \
  -f manifests/kube-vip/kube-vip-rbac.yaml \
  -f manifests/kube-vip/kube-vip-daemonset.yaml
```

The resulting DaemonSet status was:

```text
DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE
3         3         3       3            3
```

One pod ran on each control-plane node:

```text
arm64-01   Running
arm64-02   Running
arm64-03   Running
```

## VIP Verification

The VIP responded successfully:

```bash
ping -c 3 192.168.2.50
```

Captured result:

```text
3 packets transmitted
3 packets received
0.0% packet loss
```

The Kubernetes API readiness endpoint succeeded:

```bash
kubectl \
  --server=https://192.168.2.50:6443 \
  get --raw=/readyz
```

Captured result:

```text
ok
```

At verification time, `arm64-01` owned the VIP:

```text
arm64-01   192.168.2.50/32
arm64-02   VIP not hosted here
arm64-03   VIP not hosted here
```

The active owner is expected to change during leader failover.

## Current Verified State

```text
Embedded-etcd HA:                 Enabled
Control-plane members:            arm64-01, arm64-02, arm64-03
API certificates include VIP:     Yes
kube-vip DaemonSet:               3/3 Ready
API VIP:                          192.168.2.50
API VIP readiness:                ok
VIP owner at verification time:   arm64-01
MetalLB service handling:         Unchanged
```

At the point captured here, kube-vip was operational. Verify the repository
endpoint and exported kubeconfig before claiming that every client has been cut
over from `.51` to `.50`:

```bash
grep '^k3s_api_endpoint:' \
  inventory/group_vars/all.yml

kubectl config view --minify \
  -o jsonpath='{.clusters[0].cluster.server}{"\n"}'
```

The final desired values are:

```text
k3s_api_endpoint: 192.168.2.50
https://192.168.2.50:6443
```

## Final Endpoint Cutover

After kube-vip is healthy, update:

```yaml
k3s_api_endpoint: 192.168.2.50
```

Retain both SAN entries:

```yaml
k3s_tls_sans:
  - 192.168.2.51
  - 192.168.2.50
```

Run the complete playbook so servers, agents, and the exported kubeconfig use
the VIP:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/k3s.yml \
  --vault-id kalaxy3@prompt
```

If the agent template task does not yet notify a restart handler, restart the
agents one at a time after their configuration changes:

```bash
ssh pi@192.168.2.54 \
  'sudo systemctl restart k3s-agent'

kubectl wait \
  --for=condition=Ready \
  node/arm64-04 \
  --timeout=120s

ssh pi@192.168.2.55 \
  'sudo systemctl restart k3s-agent'

kubectl wait \
  --for=condition=Ready \
  node/arm64-05 \
  --timeout=120s
```

## Rebuilding the Cluster

A rebuild must handle this dependency:

> The VIP cannot be used before kube-vip is running, but kube-vip cannot run
> until at least one Kubernetes server exists.

Do not configure a brand-new first server to depend exclusively on
`192.168.2.50`.

### Recommended variable separation

Refactor the inventory so the initial bootstrap endpoint and permanent API
endpoint are explicit:

```yaml
k3s_bootstrap_endpoint: 192.168.2.51
k3s_api_endpoint: 192.168.2.50
k3s_api_vip: 192.168.2.50
k3s_api_interface: eth0

k3s_tls_sans:
  - 192.168.2.51
  - 192.168.2.50
```

Use `k3s_bootstrap_endpoint` only to establish the first server. Use
`k3s_api_endpoint` for the remaining servers, agents, and exported kubeconfig
after kube-vip is operational.

### Recommended rebuild phases

#### Phase 1: Bootstrap `arm64-01`

Render the first server with:

```yaml
cluster-init: true
tls-san:
  - "192.168.2.51"
  - "192.168.2.50"
```

Do not add a `server:` entry to the first server.

Install K3s and wait for:

```bash
sudo k3s kubectl get --raw=/readyz
```

Expected:

```text
ok
```

#### Phase 2: Deploy kube-vip immediately

Once the first server API is healthy, apply the retained kube-vip manifests
through `.51`:

```bash
kubectl \
  --server=https://192.168.2.51:6443 \
  apply \
  -f manifests/kube-vip/kube-vip-rbac.yaml \
  -f manifests/kube-vip/kube-vip-daemonset.yaml
```

Wait for the first kube-vip pod and verify:

```bash
kubectl \
  --server=https://192.168.2.50:6443 \
  get --raw=/readyz
```

Do not continue until it returns:

```text
ok
```

#### Phase 3: Join `arm64-02` and `arm64-03` through the VIP

Render remaining servers with:

```yaml
server: "https://192.168.2.50:6443"
token: "<retrieved securely during deployment>"
tls-san:
  - "192.168.2.51"
  - "192.168.2.50"
```

Never store the real token in plain text or in documentation.

Join one control-plane server at a time and verify readiness before continuing.

#### Phase 4: Join agents through the VIP

Render each agent with:

```yaml
server: "https://192.168.2.50:6443"
token: "<retrieved securely during deployment>"
```

Join `arm64-04` and `arm64-05` after the three-member control plane is healthy.

#### Phase 5: Export the kubeconfig with the VIP

Replace the loopback API address in the exported kubeconfig with:

```text
https://192.168.2.50:6443
```

Verify:

```bash
kubectl config view --minify \
  -o jsonpath='{.clusters[0].cluster.server}{"\n"}'
```

#### Phase 6: Test failover

Identify the current VIP owner:

```bash
for ip in 192.168.2.51 192.168.2.52 192.168.2.53; do
  echo "=== $ip ==="

  ssh "pi@$ip" \
    "ip -4 address show dev eth0 |
     grep '192.168.2.50' ||
     echo 'VIP not hosted here'"
done
```

Delete the kube-vip pod on the current owner or perform a controlled reboot of
that node. Then verify:

```bash
ping -c 3 192.168.2.50
kubectl get --raw=/readyz
kubectl get nodes
```

Confirm another control-plane node now owns `192.168.2.50`.

## What Must Be Retained

Keep these files in Git:

```text
inventory/group_vars/all.yml
templates/k3s-server-config.yml.j2
templates/k3s-agent-config.yml.j2
playbooks/k3s.yml
manifests/kube-vip/kube-vip-rbac.yaml
manifests/kube-vip/kube-vip-daemonset.yaml
```

Keep these outside Git:

```text
K3s server token
Ansible Vault password
Kubeconfig containing credentials
etcd snapshot binary files
Private keys and certificates
```

The K3s server token must be backed up with the etcd snapshot because it is
required to decrypt protected bootstrap data during disaster recovery.

## Rebuild Acceptance Criteria

A rebuilt cluster is back to the intended HA state only when these checks pass:

```bash
kubectl get nodes -o wide

kubectl -n kube-system get daemonset kube-vip-ds

kubectl -n kube-system get pods \
  -l app.kubernetes.io/name=kube-vip-ds \
  -o wide

kubectl \
  --server=https://192.168.2.50:6443 \
  get --raw=/readyz

kubectl config view --minify \
  -o jsonpath='{.clusters[0].cluster.server}{"\n"}'
```

Expected outcome:

```text
Five nodes Ready
Three control-plane/etcd members
Three kube-vip pods Ready
VIP API readiness returns ok
Kubeconfig endpoint is https://192.168.2.50:6443
MetalLB remains responsible for service LoadBalancer addresses
```

## Security Notes

This page intentionally excludes:

- The K3s server token
- Ansible Vault credentials
- Kubeconfig certificate data
- Private keys
- etcd snapshot contents

The addresses shown are private RFC 1918 LAN addresses and do not expose the
cluster directly to the public Internet.
## Final API Endpoint Cutover

After kube-vip was verified at `192.168.2.50`, the repository API endpoint was changed from the first control-plane node to the floating VIP:

```yaml
k3s_api_endpoint: 192.168.2.50
```

The original node address remains in the TLS SAN list for transitional and direct-node administrative access:

```yaml
k3s_tls_sans:
  - 192.168.2.51
  - 192.168.2.50
```

The full K3s playbook was then reconciled so that the control-plane nodes, agents, and generated kubeconfig use the HA API endpoint.

### Agent Restart Handling

The K3s agent play was updated so configuration changes restart each agent automatically:

```yaml
- name: Write K3s agent configuration
  ansible.builtin.template:
    src: ../templates/k3s-agent-config.yml.j2
    dest: /etc/rancher/k3s/config.yaml
    mode: '0600'
  no_log: true
  notify: Restart K3s agent
```

The agent play now includes:

```yaml
- name: Apply pending K3s agent restart
  ansible.builtin.meta: flush_handlers
```

and:

```yaml
handlers:
  - name: Restart K3s agent
    ansible.builtin.systemd:
      name: k3s-agent
      state: restarted
```

The agent play uses `serial: 1`, ensuring that agent nodes are updated one at a time.

### Agent Endpoint Verification

The live configuration on both agents was verified:

```text
arm64-04:
server: "https://192.168.2.50:6443"

arm64-05:
server: "https://192.168.2.50:6443"
```

This confirms that the agents no longer depend on `arm64-01` as their configured registration endpoint.

### Generated Kubeconfig Protection

The generated administrative kubeconfig contains cluster credentials and must not be stored in Git.

The following ignore rule was added:

```gitignore
/infrastructure/k3s-homelab/kubeconfig-kalaxy3.yaml
```

The existing tracked copy was removed from the Git index while remaining available locally:

```bash
git rm --cached \
  infrastructure/k3s-homelab/kubeconfig-kalaxy3.yaml
```

Git exclusion was verified:

```text
.gitignore:/infrastructure/k3s-homelab/kubeconfig-kalaxy3.yaml
```

The repository working tree was clean after the kubeconfig protection change.

### Repository State

The kube-vip implementation and documentation were committed and pushed to the Kalaxy3 `main` branch.

The implementation includes:

```text
inventory/group_vars/all.yml
templates/k3s-server-config.yml.j2
playbooks/k3s.yml
manifests/kube-vip/kube-vip-rbac.yaml
manifests/kube-vip/kube-vip-daemonset.yaml
markdown/k3s-api-ha-kube-vip.md
```

The later agent restart-handler update was committed separately.

### Current K3s Foundation Status

```text
Three-member embedded-etcd cluster:    Complete
Three-member control plane:            Complete
kube-vip DaemonSet:                    3/3 Ready
Floating API VIP:                      192.168.2.50
Control-plane certificates include VIP: Yes
Server endpoint migration:             Complete
Agent endpoint migration:              Complete
Generated kubeconfig protection:       Complete
MetalLB service handling:              Unchanged
Observability deployment:              Not started
MinIO deployment:                      Not started
```

### Remaining kube-vip Validation

A controlled failover test should still be performed before declaring API failover fully proven.

The test should:

1. Identify the current VIP owner.
2. Delete the kube-vip pod on that node or perform a controlled node restart.
3. Confirm another control-plane node acquires `192.168.2.50`.
4. Confirm the API remains available through the VIP.

```bash
ping -c 3 192.168.2.50

kubectl \
  --server=https://192.168.2.50:6443 \
  get --raw=/readyz

kubectl get nodes
```

Expected result:

```text
API readiness: ok
All remaining nodes: Ready
VIP owned by another control-plane node
```
