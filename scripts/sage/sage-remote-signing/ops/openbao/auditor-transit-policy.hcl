# ONLY independently administered auditor controller; cannot access Architect key.
# Binding: independent Kubernetes service account, role, and custody policy.
path "transit/sign/sage-auditor/sha2-256" {
  capabilities = ["update"]
}
