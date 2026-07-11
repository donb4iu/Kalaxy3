# Upgrade Strategy

1. Read the target K3s release notes and component compatibility notes.
2. Capture and export a fresh etcd snapshot.
3. Confirm all three server nodes are Ready and etcd is healthy.
4. Upgrade one server at a time, validating quorum and workloads after each node.
5. Upgrade agents one at a time.
6. Upgrade platform Helm releases separately from K3s.
7. Record versions and results in `markdown/Infrastructure/K3s_Homelab/Phase_Notes.md`.

Do not combine operating-system, K3s, CNI, ingress, storage, and observability upgrades
into a single maintenance operation.
