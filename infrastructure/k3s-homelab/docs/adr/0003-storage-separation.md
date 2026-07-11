# ADR 0003: Separate Shared NFS and MinIO Local Storage

Status: Accepted

## Decision

Use NFS subdirectory provisioners for shared persistent volumes and dedicated local
HDD mounts for MinIO.

## Consequences

NFS and MinIO require separate backup strategies. MinIO data must never silently fall
back to the boot SSD when `/mnt/minio` is absent.
