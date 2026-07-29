# Kalaxy3 repository instructions

Every implementation, repair, investigation, documentation change, or
evidence request begins with repository-owned SAGE discovery.

From the repository root, run:

```bash
python3 scripts/sage/sage-change-preflight.py \
  --request "<the request exactly as received>"
```

The requester is not responsible for enumerating Kalaxy3 governance rules.

Before editing:

1. Read every authoritative file reported by the preflight.
2. Run every reported baseline check.
3. Resolve guardrail failures before implementing the requested change.
4. Use repository-owned registries, locks, templates, and automation.
5. Treat committed, reviewable, inactive work as a staged implementation.
6. Do not activate or deploy until all reported validation passes.
7. Preserve terminal evidence and use the repository-owned SAGE
   publication process.

When resuming existing work, also run:

```bash
python3 scripts/sage/sage-change-preflight.py --changed
```

Do not bypass discovery because a branch already contains implementation
code.

## Enforced repository entry points

Use the repository-root commands for normal work:

```bash
SAGE_REQUEST="<the request exactly as received>" make sage-preflight
make sage-changed
make sage-guardrails
```

The homelab guardrail chain and GitHub validation also execute the
repository-owned discovery guardrail.

## Automatic SAGE evidence generation

The requester does not have to ask with the canonical SAGE wording.

When a request asks to document, preserve, chronicle, or create evidence
for completed work, automatically prepare evidence-generation inputs with:

```bash
SAGE_REQUEST="<request exactly as received>" make sage-evidence-prepare
```

Use the generated bundle to create one schema 1.2 SAGE package. The result
must be at least as complete as the canonical request in
`markdown/templates/sage-evidence-generation-request.md` and must pass:

```bash
SAGE_PACKAGE=~/Downloads/<package>.zip make sage-evidence-check
```

Do not ask the requester to restate schema, template, metadata, evidence,
navigation, checksum, or publication requirements.
