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
