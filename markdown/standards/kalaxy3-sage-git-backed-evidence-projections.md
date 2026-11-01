# Kalaxy3 SAGE — Git-backed evidence and disposable navigation

**Architect decision:** the Git repository owns source files, content hashes,
commit lineage, and revision history. GitHub Issues and Projects own the work
contract, activity, assignment and approvals. SAGE owns semantic interpretations,
causal relationships and evidence-backed lessons, persisted through governed Git.

Evidence navigation catalogs are **derived presentation artifacts**, not an
independent authoritative store and not a reason to block unrelated engineering
work when their committed copies are stale.

## Enforced execution boundary

- `make sage-index-check` validates **authoritative source evidence** and its
  record/schema integrity in memory. It does not require committed generated
  views to match current source files.
- `make docs-mkdocs-prepare` regenerates evidence catalogs and navigation into
  ignored `.mkdocs-work/source` from current Git-backed source documents. It
  records the Git revision used to build those disposable projections.
- MkDocs navigation and evidence-link validation still operate against the
  generated staged views; publication must not silently omit source records.
- `sage-index.py check` remains an explicit legacy comparison tool, but is not
  an engineering acceptance or promotion gate.
- No manual regeneration or bulk commit of derived catalogs is required for
  an ordinary implementation change.

## Compatibility obligations

Historical tracked catalog snapshots are **not removed in this correction**:
legacy evidence publication, retrieval and navigation consumers still reference
them. They are not to be treated as a second source of truth. Migration of
those remaining consumers to on-demand Git-backed retrieval is a separate,
explicitly testable compatibility obligation; do not delete their data or
silently claim the migration has already occurred.

The repository-owned Project/RACI Definition of Done continues to govern every
participant and SAGE itself. Break-glass validation must record any exceptions
and must not convert unexecuted checks into PASS.
