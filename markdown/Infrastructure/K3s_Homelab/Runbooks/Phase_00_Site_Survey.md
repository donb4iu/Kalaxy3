# Phase 0 Site Survey Runbook

Run from `infrastructure/k3s-homelab`:

```bash
make install
make syntax
make phase-0
```

Reports are written to `artifacts/site-survey/` and are intentionally ignored by Git.
Review each host report for:

- correct Ubuntu version and architecture;
- at least 7 GB detected RAM;
- synchronized time;
- expected network interface and IP;
- no active MicroK8s or previous K3s installation;
- no unexpected listeners on K3s/etcd ports;
- correct boot SSD and one-terabyte MinIO HDD identity;
- `/mnt/minio` mounted with at least 800 GB free;
- both NFS exports visible;
- firewall state understood.

Record the decision in `markdown/Infrastructure/K3s_Homelab/Phase_Notes.md`. Phase 0 makes no intentional remote
changes, although it writes local report files on the Mac.
