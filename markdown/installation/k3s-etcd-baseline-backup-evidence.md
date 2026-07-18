# K3s etcd Baseline Backup Evidence

**Project:** Kalaxy3  
**Cluster:** Kalaxy3 K3s homelab  
**Control-plane node:** `arm64-01`  
**Evidence date:** July 16, 2026  
**Status:** Completed and verified  

## Purpose

This page records the creation, export, verification, and Git exclusion of a
baseline K3s embedded-etcd snapshot.

The documentation is safe to publish because it does not contain:

- The K3s server token
- Kubeconfig credentials
- Private keys
- Certificates
- Publicly routable infrastructure addresses
- Snapshot binary content

The control-plane address is represented as `<CONTROL_PLANE_IP>` in reusable
commands. The backup artifacts remain outside Git tracking.

## Outcome

The following controls were completed successfully:

1. A named K3s etcd baseline snapshot was created.
2. Existing scheduled snapshots were confirmed.
3. The K3s server token was copied to a protected local backup directory.
4. The baseline snapshot was copied from the control-plane node.
5. Local backup permissions were restricted.
6. The remote and local SHA-256 checksums matched.
7. The entire `backups/` directory was confirmed as ignored by Git.

## Backup Artifacts

| Artifact | Local location | Permissions | Git status |
|---|---|---:|---|
| Baseline etcd snapshot | `backups/kalaxy3-baseline-20260716-180040-arm64-01-1784242841` | `0600` | Ignored |
| K3s server token | `backups/k3s-server-token.txt` | `0600` | Ignored |
| Backup directory | `backups/` | `0700` | Ignored |

> The K3s server token is required during disaster recovery because it protects
> bootstrap data associated with the snapshot. Its value must never be placed in
> source control or published documentation.

## Step 1: Create the Baseline Snapshot

The snapshot was created on the `arm64-01` K3s server:

```bash
ssh pi@<CONTROL_PLANE_IP> \
  'sudo k3s etcd-snapshot save \
  --name kalaxy3-baseline-$(date +%Y%m%d-%H%M%S)'
```

### Captured result

```text
level=info msg="Snapshot kalaxy3-baseline-20260716-180040-arm64-01-1784242841 saved."
```

The resulting snapshot size was:

```text
13324320 bytes
```

## Step 2: Confirm Snapshot Inventory

The snapshot inventory was queried with:

```bash
ssh pi@<CONTROL_PLANE_IP> \
  'sudo k3s etcd-snapshot list'
```

### Captured snapshot inventory

```text
Name                                                 Size      Created
etcd-snapshot-arm64-01-1784048405                    13324320  2026-07-14T12:00:05-05:00
etcd-snapshot-arm64-01-1784091602                    13324320  2026-07-15T00:00:02-05:00
etcd-snapshot-arm64-01-1784134802                    13324320  2026-07-15T12:00:02-05:00
etcd-snapshot-arm64-01-1784178004                    13324320  2026-07-16T00:00:04-05:00
etcd-snapshot-arm64-01-1784221202                    13324320  2026-07-16T12:00:02-05:00
kalaxy3-baseline-20260716-180040-arm64-01-1784242841 13324320  2026-07-16T18:00:41-05:00
```

This confirmed that the manual baseline snapshot existed alongside the existing
scheduled snapshots.

## K3s Snapshot Command Warnings

The snapshot commands displayed warnings similar to:

```text
Unknown flag --write-kubeconfig-mode found in config.yaml, skipping
Unknown flag --node-ip found in config.yaml, skipping
Unknown flag --advertise-address found in config.yaml, skipping
Unknown flag --cluster-cidr found in config.yaml, skipping
Unknown flag --service-cidr found in config.yaml, skipping
Unknown flag --cluster-dns found in config.yaml, skipping
Unknown flag --tls-san found in config.yaml, skipping
Unknown flag --disable found in config.yaml, skipping
Unknown flag --cluster-init found in config.yaml, skipping
```

These warnings did not prevent the operation. The `etcd-snapshot` subcommand
read the shared K3s configuration and skipped settings that apply to the K3s
server process rather than the snapshot subcommand.

Successful completion was established by both:

```text
Snapshot kalaxy3-baseline-20260716-180040-arm64-01-1784242841 saved.
```

and the presence of the snapshot in the subsequent inventory.

## Step 3: Create the Protected Local Backup Directory

```bash
repo_dir="$HOME/dvlp/Kalaxy3"
backup_dir="$repo_dir/backups"

mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
umask 077
```

The directory permissions prevent access by other local users.

## Step 4: Export the K3s Server Token

```bash
ssh pi@<CONTROL_PLANE_IP> \
  'sudo cat /var/lib/rancher/k3s/server/token' \
  > "$backup_dir/k3s-server-token.txt"
```

The token value is intentionally excluded from this evidence page.

## Step 5: Exclude Backup Material from Git

The following repository-root rule was added to `.gitignore`:

```gitignore
/backups/
```

This rule ignores only the `backups` directory at the root of the Kalaxy3
repository.

## Step 6: Copy the Snapshot Off the Control-Plane Node

```bash
snapshot_name="kalaxy3-baseline-20260716-180040-arm64-01-1784242841"
snapshot_path="/var/lib/rancher/k3s/server/db/snapshots/$snapshot_name"

ssh pi@<CONTROL_PLANE_IP> \
  "sudo cat '$snapshot_path'" \
  > "$backup_dir/$snapshot_name"

chmod 600 \
  "$backup_dir/$snapshot_name" \
  "$backup_dir/k3s-server-token.txt"
```

This created an off-node copy on the administration workstation.

## Step 7: Verify Snapshot Integrity

The SHA-256 checksum was calculated independently on the K3s node and the local
workstation:

```bash
remote_sha="$(
  ssh pi@<CONTROL_PLANE_IP> \
    "sudo sha256sum '$snapshot_path'" |
    awk '{print $1}'
)"

local_sha="$(
  shasum -a 256 "$backup_dir/$snapshot_name" |
    awk '{print $1}'
)"

printf 'Remote: %s\nLocal:  %s\n' "$remote_sha" "$local_sha"

test "$remote_sha" = "$local_sha" &&
  echo "Snapshot verified successfully."
```

### Captured verification evidence

```text
Remote: 9b0446254fe8c84eb3578efcab8403c06bcf3535a4c49a9ea9f1febbc960da69
Local:  9b0446254fe8c84eb3578efcab8403c06bcf3535a4c49a9ea9f1febbc960da69
Snapshot verified successfully.
```

The matching checksums establish that the local snapshot is byte-for-byte
identical to the snapshot stored on `arm64-01`.

## Step 8: Verify Git Exclusion

```bash
git -C "$repo_dir" check-ignore -v \
  "backups/$snapshot_name" \
  "backups/k3s-server-token.txt"

git -C "$repo_dir" status --short --ignored backups
```

### Captured Git evidence

```text
.gitignore:223:/backups/ backups/kalaxy3-baseline-20260716-180040-arm64-01-1784242841
.gitignore:223:/backups/ backups/k3s-server-token.txt
!! backups/
```

This confirmed that both recovery artifacts and the containing directory were
excluded from Git tracking.

## Security Controls

The following protections were applied:

- `umask 077` ensured newly created backup files were private by default.
- The backup directory was explicitly set to mode `0700`.
- The snapshot and server token were explicitly set to mode `0600`.
- The backup directory was excluded at the repository root.
- No secret value was copied into this documentation.
- The snapshot was validated before being accepted as a recovery artifact.

## Recommended Repository Check

Before pushing documentation changes, run:

```bash
git -C "$HOME/dvlp/Kalaxy3" status --short
git -C "$HOME/dvlp/Kalaxy3" diff --cached
```

The output must not list:

```text
backups/k3s-server-token.txt
backups/kalaxy3-baseline-20260716-180040-arm64-01-1784242841
```

## Recovery Readiness Result

**PASS**

As of July 16, 2026:

- The embedded-etcd state was captured.
- The snapshot was copied off the control-plane node.
- The snapshot integrity was verified.
- The matching K3s server token was preserved.
- Recovery artifacts were protected from accidental publication.
