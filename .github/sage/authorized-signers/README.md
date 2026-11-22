# Trusted SAGE audit signing keys

An Architect-controlled **prior trusted-base** change must place two PUBLIC PEM
keys here before enabling this check as a required branch-protection status:

- `auditor.pem` — independent SAGE auditor/controller; can sign `executed`.
- `architect.pem` — Architect-held identity; can sign `bypassed` or `not_applicable`.

Never commit private keys or let the persistent/implementation LLM access them.
The check loads keys exclusively from the trusted PR base, never from the PR.
A digest is integrity metadata; the signature is the authorization binding.
The signer is accountable for validating that an actual independent review took
place before signing `executed`. This check validates the attestation and its
source artifact; it does not impersonate the isolated auditor.

The repo's existing RACI remains authoritative. Assigning public keys to these
roles must itself go through that established Architect authorization process.
