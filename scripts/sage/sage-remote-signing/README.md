# SAGE PR #61 audit accountability — OpenBao/Cloudflare integration

**Classification:** untrusted, locally tested **implementation candidate** for the
existing audit-accountability activation. **Not deployed, admitted, or enforced.**
No Keycloak, new RACI model, role redesign, or extra objective.

## Verified existing contract (captured authoritative `main`)

- `main`: `47124f339cb3a1c163fce7456ecf859eb069d41e`
- `scripts/ci/sage_audit_receipt.py` SHA-256:
  `04c4b5c1502ed5f01585f9db06dc5b78abff387400ad90102bf8c3a7afbc3e19`
- Source capture ZIP SHA-256:
  `4d232c01c065ffeff8d616e7bdac8e802a4b2587873ea359990fab24b095c398`
- Receipt format: `sage-pr-audit-receipt-v1`; JSON sorted keys, compact separators,
  newline; SHA-256; RSA PKCS#1 v1.5; raw `.sig` bytes.
- Executed audit: **independent auditor** signs; must reference committed audit
  evidence. Bypassed / not applicable: **Architect** signs with justification.
- The closeout commit trailer is exactly `SAGE-Audit-Receipt-SHA256: <digest>`;
  source scope excludes `.sage/audit-receipts/` so the receipt can be committed
  after the reviewed implementation and its evidence.
- CI runs from trusted `pull_request_target` base, loads only trusted-base
  public keys from `.github/sage/authorized-signers`, and must be separately
  configured as a required branch check after end-to-end qualification.

## Added integration (candidate)

1. `sage_signing/` — two-step Cloudflare Access-authenticated signing controller;
   canonical PR #61 JSON input only, a fixed signer role, a persistent one-time
   authorization ledger, and OpenBao Transit RSA-3072/SHA-256 signing.
2. `pr61_remote_issue.py` — consumes the **existing** verifier from the trusted
   base after checking its SHA-256; uses its `issue_payload` and `encode` rules;
   calls the remote signing client; checks the returned RSA signature against
   the **prior trusted-base public key**; writes only the `.json` and binary
   `.sig` files. Does not issue its own evidence or claim auditor qualification.
3. `ops/openbao/` — separate, sign-only Architect and auditor policies.
4. `ops/k8s/` — deliberately non-applicable controller templates for **separate**
   auditor and Architect namespaces, identities, and keys. No raw OpenBao
   or Kubernetes API is made publicly accessible.
5. `tests/` — offline Access/RSA/role-boundary tests and real Git/OpenSSL
   end-to-end PR #61 verifier integration (including negative cases).
6. `stage-local.command` — creates and tests an isolated checkout at the exact
   captured `main` after fetching remote `main`; makes a **local commit only**.

## Operator: stage this candidate against Kalaxy3 `main`

Unzip the archive into `~/Downloads`, then:

```bash
bash ~/Downloads/sage-audit-pr61-openbao-integrated/stage-local.command
```

**Git staging correction:** after cloning, explicitly fetch the validated
`origin/main` commit from the source checkout. A local clone does not
automatically include newer remote-tracking-only commits.

It refuses to proceed if remote `main` has moved beyond the captured commit or
if PR #61's trusted verifier changed. It records complete test output in a
Downloads log. No `git push`, merge, cluster change, key generation or GitHub
settings mutation occurs.

## Issuing a real receipt (ONLY after trusted public key admission and deployment)

Two separate Cloudflare Access applications and OpenBao Transit keys are
required. `SAGE_SIGN_URL` is the actual Access-protected signer **for the
intended role**. The auditor controller must be independently administered and
must not accept the Architect's Access identity or hold the Architect key.

```bash
export SAGE_SIGN_URL='https://<approved-signing-app-hostname>'
python3 scripts/sage/sage-remote-signing/pr61_remote_issue.py \
  --repo . --base origin/main --objective '#50' \
  --disposition executed --audit-path 'path/to/committed-auditor-evidence.json' \
  --purpose 'Independent auditor qualified this exact PR source scope'
```

For an Architect-approved bypass, use `--disposition bypassed`, supply a
meaningful `--reason`, and authenticate against the **Architect** application.
The CLI requires terminal confirmation of the exact SHA-256 and refuses to
proceed if the signer returns the wrong identity, padding, or public-key
signature. The operator must still stage and commit the generated two files
with the printed exact trailer through existing governed Git lifecycle.

## Actual work remaining (do not claim these were performed)

1. **Protected signing service:** Install an official, pinned OpenBao release
   in Kalaxy3 after selecting verified storage and TLS, arranging durable Raft
   backup/recovery and custodian-controlled init/unseal, and validating network
   isolation. `helm` was **unavailable** during source capture.
2. **Independent custody:** Create the Architect key in protected OpenBao
   Transit. An independently controlled auditor must create/hold its separate
   key; merely using a second Kubernetes service account is *not proof of
   independent administration*. No signing private key belongs in Git/LLM
   context. Retain existing encrypted Mac Architect key until replacement is
   proven.
3. **Remote authentication:** Bind each controller to an independently governed
   Cloudflare Access application and verified MFA policy. Audit the chosen
   session duration; the controller's digest confirmation **does not prove
   fresh, per-transaction MFA**. Validate Access JWT at the origin, not an
   untrusted email header. Do not expose OpenBao through the public tunnel.
4. **Trust admission:** Verify real signatures with exported public keys, then
   admit *only* authorized public keys to prior trusted `main` via existing
   governance. Required check stays disabled until then.
5. **PR qualification:** Verify real `executed`, `bypassed`, invalid signature,
   changed source, expired intent, wrong role, auditor independence, remote
   off-LAN connectivity, outage/recovery and PR check appearance. Configure
   branch protection and admin bypass restrictions separately.
6. **RACI integration boundary:** PR #61 verifies that an authorized role
   signed a scope/evidence-bound receipt. It **does not itself inspect the
   contents of the independent audit evidence, invoke narration/observation,
   or automatically remediate deficient work**. Those existing SAGE role
   processes still need to supply real reviewed evidence before the independent
   auditor signs. Never treat a receipt alone as complete RACI remediation.

## Environment and reference material

Deployment requires inspected values for the namespace, TLS CA, trusted Access
AUD, exact controller image digest, working storage class, network policy,
Kubernetes auth role, custodian, recovery procedures and reachable service
route. No placeholder config may be applied to the live cluster.

- [OpenBao Transit API](https://openbao.org/docs/api/secret/transit/)
- [OpenBao HA with Raft](https://openbao.org/docs/platform/k8s/helm/examples/ha-with-raft/)
- [Cloudflare Access JWT validation](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/)

## Reproducible offline verification

Use the actual verifier at `main` (or captured trusted source) and install
`requirements-dev.txt` in an isolated venv. From this package directory:

```bash
SAGE_PR61_SOURCE=/path/to/main/scripts/ci/sage_audit_receipt.py \
  PYTHONPATH=. python3 -m unittest discover -s tests -v
```

The separate existing `tests/ci/test_sage_audit_receipt.py` suite must also
pass from the Kalaxy3 checkout. No test substitutes for a live OpenBao-backed,
independently authorized PR receipt or GitHub required-check verification.

**Existing infrastructure evidence:** the captured K3s inventory lists an
`external-access/cloudflared` deployment, but no OpenBao deployment or chart
was observed. The existing Cloudflare validation playbook explicitly reports
`authorized_mfa_access_verified: false` for machine-generated validation;
MFA assurance requires a real authorized operator check rather than assuming
Cloudflare's presence proves it.
