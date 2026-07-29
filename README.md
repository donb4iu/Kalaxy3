# Kalaxy3

Mixed AMD64 and ARM64 homelab based on k3s.

## Documentation publication

Markdown under `markdown/` is the canonical documentation source.

The repository workflow builds and strictly validates the pinned MkDocs
Material toolchain, promotes the verified static site into `docs/`, publishes
that directory to `donb4iu.github.io/docs/Kalaxy3`, and builds the same
generated output into the Kalaxy3 nginx documentation image.

Repository entry points:

```bash
make docs-mkdocs-stage
make docs-mkdocs-publication-test
make docs-mkdocs-generate
```

Generated files under `docs/` are workflow-owned publication output and should
not be edited manually.

## SAGE change discovery

Every repository change begins with automatic SAGE context discovery:

```bash
python3 scripts/sage/sage-change-preflight.py \
  --request "<the request exactly as received>"
```

See [SAGE.md](SAGE.md) for the repository-owned change process.
