# Kalaxy3 SAGE publisher

Normal use from the repository root:

```bash
python3 scripts/sage/sage-publish.py check ~/Downloads/<package>.zip
python3 scripts/sage/sage-publish.py publish ~/Downloads/<package>.zip --push
```

Run the isolated end-to-end test:

```bash
python3 scripts/sage/sage-publish.py self-test
```

The governing process is:

```text
markdown/standards/kalaxy3-sage-evidence-publication-process.md
```
