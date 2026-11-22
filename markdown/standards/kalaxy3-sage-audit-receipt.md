# SAGE — Signed audit accountability at governed Git closeout

**Purpose:** Preserve Architect authority and independent auditor accountability
without making the auditor's architectural recommendation a mandatory outcome.

The delegated Git adapter records a SHA-256 trailer in the closeout commit. The
receipt bytes live in governed Git; the SHA-256 proves integrity, and a signature
from an authorized role proves which identity attested to the disposition.

The receipt must have exactly one of these dispositions:

- `executed`: References an existing committed audit artifact, signed using the
  independent auditor/controller key.
- `bypassed`: Architect-signed with a documented justification.
- `not_applicable`: Architect-signed with a documented justification.

The receipt binds to a reviewed predecessor commit and to the Git tree delta
from its merge-base, excluding only `.sage/audit-receipts/**`. A receipt-only
closeout commit leaves that scope unchanged. Source edits, code edits, or
retrieval-evidence changes after signing invalidate verification; the review
must be repeated or a revised Architect disposition signed.

The verifier reads trusted public keys ONLY from the protected PR base. It
checks a single `SAGE-Audit-Receipt-SHA256: <64hex>` trailer on the PR head,
exact SHA-256 receipt and referenced evidence, the role-specific OpenSSL
signature, ancestry and diff scope. It does not execute PR code, edit Git,
authorize a merge, or certify an auditor's recommendation as correct.

## Authority and lifecycle

The Architect owns role-to-public-key admission under the **existing** Kalaxy3
RACI; neither the persistent LLM nor an implementation role may provision keys,
forge an audit, or self-authorize bypass. Private keys must remain outside Git
in existing approved secret custody (e.g. Vault). For `executed`, the trusted
audit controller must not sign unless the independent role actually ran and
its source-bound result is committed. Signing is an attestation of performance,
not endorsement of the advice.

The check uses `pull_request_target` to run its workflow from the trusted base, with `contents: read` token permissions. PR code is never executed. The initial installation PR has no base-branch workflow and is reviewed under existing governance; its new check only starts after merge. Protect future edits to this workflow under Architect-owned review.

The PR check may be configured as a **required branch-protection status** by
the Architect after keys and the trusted workflow are deployed. That requires
recording execution or justified bypass, but not favorable audit findings.

Original objective/query evidence may be included by `--original-query-ref`.
This preserves a concrete replay target; automatic post-ingestion query replay
is a separate existing-SAGE lifecycle integration and is not claimed by this
receipt verifier. Do not silently infer improved recall from review success.

## Non-goals

No LLM-driven Git mutations; no parallel role taxonomy; no new GitHub connector;
no auto PR creation or merging; no Neo4j changes; no new enforcement of WAR/CAF
opinions. Cryptographic signatures attest accountable disposition but do not
prove audit semantic quality; honest separation is essential.
