# Kalaxy3 K3s Homelab

Phased Ansible deployment for five Raspberry Pi 4 nodes with future Intel expansion.

## Topology

- K3s servers: `192.168.2.51-53`
- K3s agents: `192.168.2.54-55`
- Future Intel agents: `192.168.2.61-63`
- NFS server: `192.168.2.7`
- MetalLB pool: `192.168.2.20-49`

## Safe starting point

```bash
make install
make syntax
make phase-0
```

Phase 0 performs a non-modifying site survey and writes local reports under
`artifacts/site-survey/`. Review `markdown/Infrastructure/K3s_Homelab/Runbooks/Phase_00_Site_Survey.md` before running
Phase 1.

## Phases

```bash
make phase-1
make validate-1
make phase-2
make validate-2
make phase-3
make validate-3
make phase-4
make validate-4
make phase-5
make validate-5
make phase-6
make validate-6
```

Phase 7 is an explicit security, DNS, TLS, backup, and Cloudflare design gate. Phase 8
adds future Intel nodes.

## Documentation

- `markdown/Infrastructure/K3s_Homelab/01_Architecture.md`
- `markdown/Infrastructure/K3s_Homelab/02_IP_Address_Plan.md`
- `markdown/Infrastructure/K3s_Homelab/03_Deployment_Order.md`
- `markdown/Infrastructure/K3s_Homelab/Architecture_Decisions/`
- `markdown/Infrastructure/K3s_Homelab/Runbooks/`
- `markdown/Infrastructure/K3s_Homelab/04_Phased_Deployment.md`
- `markdown/Infrastructure/K3s_Homelab/Phase_Notes.md`

Never expose management services using router port forwarding. Do not commit
kubeconfigs, plaintext secrets, Vault passwords, Cloudflare credentials, or generated
site-survey reports.
