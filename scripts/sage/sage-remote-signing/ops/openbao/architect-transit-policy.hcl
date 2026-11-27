# ONLY the Architect signing controller's OpenBao Kubernetes-auth role.
# No reads, key creation, export, deletion, rotation or administrative rights.
path "transit/sign/sage-architect/sha2-256" {
  capabilities = ["update"]
}
