# IP Address Plan

| Range or address | Purpose |
|---|---|
| `192.168.2.1` | LAN gateway |
| `192.168.2.7` | NFS/SMB server |
| `192.168.2.8` | Mac Mini Ansible controller |
| `192.168.2.20-49` | MetalLB pool; must remain outside DHCP |
| `192.168.2.51-55` | Raspberry Pi K3s nodes |
| `192.168.2.61-63` | Future Intel K3s nodes |

Reserve every infrastructure address in DHCP or configure it statically. Do not let
DHCP allocate any address from the MetalLB pool.
