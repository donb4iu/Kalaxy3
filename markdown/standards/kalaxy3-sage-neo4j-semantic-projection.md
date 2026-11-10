# Issue #50 — Neo4j semantic query projection (engineering candidate)

This is a bounded **candidate implementation**, not an approved semantic ontology, an autonomous planner, or a new SAGE authority store. The authoritative engineering work contract is [Kalaxy3 Issue #50](https://github.com/donb4iu/Kalaxy3/issues/50). Architect approval for implementation does not authorize production deployment, promotion to `main`, or changes to Architect-owned scope.

## Contracts and data boundaries

- `scripts/sage/sage_neo4j_inventory.py`: read-only pinned Git-tree inventory; identifies **every** tracked Git object and SHA-256 digests of its committed bytes. Reads only metadata into Neo4j, never source bodies, credentials or evidence text. Unreadable/binary sources remain counted. Rebuild uses exact commit revision.
- `sage-semantic-concepts.json`: existing SAGE concept vocabulary; concepts with no evidence remain independent nodes. Path aliases produce **unverified candidates**, not accepted semantic facts.
- `scripts/sage/sage_neo4j_lifecycle.py`: exact source count and reverse-relationship checks, scoped evidence-presence state, bounded model revision repair and externally verified activation policy interface.
- `scripts/sage/sage_neo4j_projection.py`: version-scoped Neo4j graph projection with readback and unique keys. Does not implement `activate`, `publish`, `promote`, merge or production deployment. `SageProjection` remains `candidate`.
- `scripts/sage/sage-neo4j-projection.py`: explicit local-only Neo4j integration CLI. Never accepts remote Bolt servers in this first slice.

**Source authority** remains governed Git and externally authoritative systems. A Neo4j graph is a disposable query view. The Git parent and evidence source revision are included in the projection identity. Even a successful matching query is not evidence-maturity adjudication.

## Execution (isolated engineering branch)

```bash
python3 -m unittest discover -s scripts/sage -p test_sage_neo4j.py -v
```

For isolated local Neo4j integration testing, install the pinned official `neo4j` driver from `requirements-sage-neo4j.txt` in a separate venv. Supply local `SAGE_NEO4J_PASSWORD` and a loopback Bolt endpoint:

```bash
python3 scripts/sage/sage-neo4j-projection.py \
  --repo . --out /tmp/sage-issue50-neo4j-evidence \
  --require-integration --concept storage
```

No live source content is copied into Neo4j. Query output only includes source paths and candidate status. Access to the local projection still requires a protected endpoint and source-level authorization before shared deployment.

## Acceptance ledger — NOT 9/9

| DoD | Status in this contribution | Remaining work before objective acceptance |
|---|---|---|
| 01 — Lossless inventory | Partial: full committed Git-tree identity and per-blob hashes | Reconcile historical 79 anchors, external evidence, independent full-coverage enumerator and current source universe |
| 02 — Semantic breadth | Partial: existing concept vocabulary and untrusted path candidates | Full corpus concept accounting, cross-cutting obligation applicability and independently reconciled mappings |
| 03 — Graph fidelity | Partial: version-scoped concept and evidence nodes, related edges | Historical solution/obligation/condition graph fidelity and cross-revision lineage |
| 04 — Evidence presence | Partial: distinguish candidate from qualified absence | Complete scoped qualification and zero-evidence assertions against independent benchmarks |
| 05 — Semantic matching | Partial: path alias candidates, exact graph readback | Contextual/paraphrase semantic matching and complete accepted bidirectional links |
| 06 — Recall benchmarks | Not complete | Independent concept/obligation corpus and negative precision/recall evaluation |
| 07 — Rebuild | Partial: exact version identity and post-write count checks | Full graph-digest equivalence, robust failed-build isolation and reconstruction comparison |
| 08 — Development/promotion synchronization | Partial: version-scoped candidate avoids active pointer | Integrate with native SAGE promotion, replay source add/change/delete and drift recovery |
| 09 — Break-glass evolution | Partial: bounded repair validation with approved changed paths | Governed end-to-end patch, RACI tests, promotion and post-activation readback |

The graph being created is only a **candidate**. No code here is allowed to declare objective success, activate a promoted graph, or bypass existing SAGE approval. The feature branch / draft PR is an engineering contribution subject to independent review and subsequent completion of remaining DoD.

## Deferred work and explicit risks

A feature-complete ontology, stand-alone vector database, Neo4j HA, and production K3s deployment remain deferred. This slice does **not** establish semantic recall from free-form human paraphrases, and Neo4j Community cannot independently enforce per-evidence read authorization for a multi-tenant shared endpoint. Therefore the first test endpoint is bound to loopback and should not publish raw evidence. Evidence classification and access controls must be qualified before any shared deployment.

Python dependencies for this slice (copyable `requirements.txt`):

```text
neo4j==6.4.1
```
