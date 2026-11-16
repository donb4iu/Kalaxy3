# SAGE Context Assembly — Bounded selection and omission challenge

**Architect objective:** Issue #54. **Prior source-discovery milestone:** Issue #55, merged PR #56. **Status:** Engineering candidate, not an accepted context or an extra governance gate.

This slice reuses the repository's `sage_context_discovery.py` source enumeration and its exact Git revisions. Its additional `sage_context_selection.py` selects attributable source pointers from existing discovery and external reviewer inputs; `sage_context_critique.py` separately traverses the entire Git tree using explicitly attributable probes. Such literal probes identify **potential omissions**; they do not prove semantic relevance, correctness or completeness.

A review JSON file can provide independently prepared source judgments, probe phrases and source-excerpt authorizations. Reviewer independence is **not authenticated by the file**. All judgments remain candidates, even if tagged as `relevant`, `historical`, `opposing` or `obligation`. Without a review record, all selected evidence remains `not_evaluated`.

No source text is exported by default. An optional excerpt requires an exact pinned source path, Git blob object ID, SHA-256 digest, `authorized=true`, plus bounded UTF-8 content and sensitive-content checks. The caller remains responsible for actual source-level authorization and reviewing output before sending it to any external LLM; filename and token pattern checks are defense-in-depth, not a formal policy engine. Reject mismatched objects and digest claims.

Output consists of:

- `selection-manifest.json`: candidate evidence, role, feature/main pins, reviewer claims, optional excerpts, source scope and uncertainties.
- `omission-challenge.json`: independent full-tree probe results outside existing nominations; unverified and bounded.
- `candidate-context.md`: safely encoded, source-attributed context references; not an approved final fresh-role packet.

No Neo4j query, Git mutation, GitHub issue publication, graph write, Kubernetes change or context-completeness assertion occurs during selection. The #50 candidate projection is neither promoted nor overwritten. External GitHub and operational sources are explicitly marked unsearched, not assumed absent.

**Success of this PR does not complete Issue #54.** Independent relevance/omission judgments, source-authorized evidence scope and real fresh-agent decision value require subsequent evidence. Avoid artificial acceptance thresholds and additional workflow gates.
