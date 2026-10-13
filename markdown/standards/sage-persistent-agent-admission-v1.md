# SAGE persistent-agent authority boundary — candidate v1

## Architect-owned objective
Architecture Helper Dashboard with secure Cloudflare remote access. GitHub Projects backlog baseline is an active dependency. This patch addresses a necessary security/control blocker and **does not** replace the parent functional objective.

## Normal operation
- The persistent LLM may provide **functional intent only**. It cannot invoke SAGE primitives, assign its execution roles, select lifecycle states, supply Git operations, or instruct source mutation.
- SAGE validates the functional handoff and decides when a fresh isolated translator is needed. The translator's context is one bounded invocation. Its output remains a proposal.
- RACI Responsible, independent Reviewer, Referee, Narrators, Path/Architecture Critic and Accountable observation evaluate whether functional work advances the backlog-owned objective.
- GitHub Projects owns backlog facts; Git owns source; SAGE owns governance/qualified evidence; the Architect owns material decisions.

## Exception
An explicit Architect break-glass authorization may scope a particular repair, with exact objective, request digest, and repair scope. The **trusted SAGE authority service**, not the persistent agent, must verify grant identity, signature/provenance, status and expiration before passing a trusted grant to `admit`. The test fixture is not proof of a deployed verification service.

## Enforcement limitations / nonclaims
- `persistent_entry_authority.py` is a fail-closed **contract gate**, with no Git or API mutation methods.
- The CLI allows functional handoffs only. It intentionally has no CLI mechanism to pass a break-glass grant. This prevents caller-supplied authority from being accepted.
- The module's `trusted_grant` parameter MUST be supplied by an independently authenticated SAGE caller, never deserialized from the persistent input or environment without verification. A `valid: true` field is NOT independently sufficient evidence.
- Strict schema validation rejects execution controls as properties. Free-form prose may still carry disguised operational directions: do not treat this implementation as sufficient semantic isolation. The existing fresh-role isolation and SAGE role boundary must also enforce that behavior.
- Existing CLI/front-door invocation paths are NOT patched by this contribution. Production enforcement requires locating each applicable entry point, applying this gate **before** role invocation, testing bypasses/alternate paths, and verifying the Architect grant authority with the repository's actual policies.
- The package intentionally avoids altering a previously promoted controller from a stale source snapshot. It is not production activated.

## Acceptance tests before promotion
1. All persistent-agent entry points reject direct control proposals without verified break-glass.
2. A legitimate functional dashboard request is accepted and routed by SAGE to a fresh translator; the persistent agent cannot choose SAGE mechanics.
3. One caller cannot manufacture or broaden its Architect authorization.
4. Existing approved deterministic continuation still works without requesting persistent-agent input.
5. Defective SAGE capability produces bounded patch recovery, and execution returns to the dashboard/backlog objective.
6. Functional progress evidence survives interruption and can be restored without relying on persistent conversation history.

## Next functional milestone
Integrate this contract at the current SAGE front door with independent grant verification and source-current regression tests, then resume the GitHub Projects baseline and Architecture Helper Dashboard delivery. Keep all uncommitted project work intact.
