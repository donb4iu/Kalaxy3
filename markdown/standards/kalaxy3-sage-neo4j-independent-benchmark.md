# SAGE Issue #50 — Independent semantic benchmark measurement

**Status:** candidate engineering contract; no Architect acceptance implied.

This benchmark is distinct from source inventory validation and Neo4j implementation unit tests. It measures only source↔concept candidate nomination against **separately produced judgments**, tied to exact Git revision and projection fingerprint. Sources not scanned for text are still accounted for. A missing historical model produces `not_evaluated`, not an evidence-absence finding. A malformed model fails closed.

## Label document

The independent assessor prepares a separate JSON file with these fields:

```json
{
  "schema": "sage-neo4j-independent-labels-v1",
  "revision": "<exact committed Git SHA>",
  "projection_fingerprint": "<exact fingerprint from readiness receipt>",
  "annotator": "<assessor identity>",
  "annotation_reference": "<independent reviewed evidence/annotation artifact>",
  "judgments": [
    {
      "path": "<tracked source path at revision>",
      "concept": "<known concept identifier>",
      "verdict": "relevant",
      "basis": "<independent rationale and source evidence locator>"
    },
    {
      "path": "<another tracked source path>",
      "concept": "<known concept identifier>",
      "verdict": "irrelevant",
      "basis": "<negative-case rationale>"
    }
  ]
}
```

Verdicts: `relevant`, `irrelevant`, `uncertain`. Annotators should find positives **independently of candidate output**, including paraphrase or synonymous content lacking vocabulary cues; sample negatives, ambiguous or misleading lexical hits, and empty-target concepts. Capture selection procedure and denominators in the annotation reference. Automated checks validate references and scope, not that an annotator is truly independent or unbiased.

Run `python3 scripts/sage/sage-neo4j-benchmark.py --repo . --out /tmp/sage-readiness.json` to capture revision-pinned source inventory counts and a readiness fingerprint. If a committed concept model is unavailable, the result remains `not_evaluated`. Only once separately reviewed labels exist use `--labels /path/to/independent-labels.json` to obtain pair-level measurement; write the output outside the repository or add it through the governed evidence lifecycle.

The report includes true and false positives, false negatives, true negatives, unresolved labels, unlabeled candidate count and null-valued metrics for undefined denominators. Precision and recall are **limited to labeled pairs**, not corpus-wide recall. Completeness of independent source/concept coverage, query paraphrase retrieval, exact established-link retrieval and Architect-accepted thresholds remain separate DOD-06/DOD-05 requirements. Nothing here promotes an edge, judges evidence maturity, marks a DoD passed or activates a projection.
