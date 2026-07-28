# Kalaxy3 SAGE publisher and evidence indexer

Validate a package:

```bash
python3 scripts/sage/sage-publish.py check ~/Downloads/<package>.zip
```

Publish and push:

```bash
python3 scripts/sage/sage-publish.py publish ~/Downloads/<package>.zip --push
```

Reconcile all current and historical evidence:

```bash
python3 scripts/sage/sage-index.py reconcile
```

Verify that generated navigation is current:

```bash
python3 scripts/sage/sage-index.py check
```

Run the isolated end-to-end test:

```bash
python3 scripts/sage/sage-publish.py self-test
```

The publisher enforces schema 1.2, canonical metadata and navigation fields,
page-level TOC presence, checksums, implementation/evidence commit separation,
and safe Git publication. The indexer preserves schema 1.0/1.1 and pre-SAGE
records, applies curated or clearly inferred discovery metadata, and generates
human and machine evidence catalogs without rewriting historical source files.

## Change discovery

Before implementation, infer repository authority from the request:

```bash
python3 scripts/sage/sage-change-preflight.py \
  --request "Add centralized logging"
```

Validate the discovery path with:

```bash
python3 scripts/sage/sage-change-discovery-guardrail.py
```

## Evidence orchestration

Prepare canonical evidence-generation inputs from ordinary requester
language:

```bash
SAGE_REQUEST="Create the evidence for this work."   make sage-evidence-prepare
```

The implementation is
`scripts/sage/sage-evidence-orchestrator.py`. It preserves the request,
applies the canonical generation request, discovers SAGE authorities,
captures repository evidence, accepts redaction-checked terminal evidence,
and creates a self-contained input ZIP outside the repository.

Validate a generated package through the existing publisher:

```bash
SAGE_PACKAGE=~/Downloads/<package>.zip make sage-evidence-check
```
