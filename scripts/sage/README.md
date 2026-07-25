# Kalaxy3 SAGE publisher

Validate a package:

```bash
python3 scripts/sage/sage-publish.py check ~/Downloads/<package>.zip
```

Publish and push:

```bash
python3 scripts/sage/sage-publish.py publish ~/Downloads/<package>.zip --push
```

Self-test:

```bash
python3 scripts/sage/sage-publish.py self-test
```

The publisher enforces record schema 1.1, the exact front-matter order, the
canonical Record metadata table, Five-W consistency, artifact checksums,
implementation/evidence commit separation, and safe Git publication.
