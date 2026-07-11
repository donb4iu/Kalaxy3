# ADR 0002: MetalLB with Traefik

Status: Accepted

## Decision

Disable K3s ServiceLB, retain bundled Traefik, and use MetalLB layer-2 advertisement
for LAN-facing `LoadBalancer` services.

## Consequences

The MetalLB pool must be reserved outside DHCP. Router port forwarding is prohibited
for cluster management services.
