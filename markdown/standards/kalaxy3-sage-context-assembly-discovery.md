# SAGE context assembly — first bounded evidence discovery adapter

**State:** Engineering contribution; no context-completeness certification and no new merge/approval gate.

## Architectural contract

SAGE uses the existing native Git/evidence lineage and Issue #50 query projection to find source *candidates* for an Architect objective. A fresh agent does not inherit a persistent agent's untested conclusions. Sources and relationships are presented with explicit provenance, qualification, temporal boundaries and unknowns. The current slice only creates a **source-reference envelope**; it does not make semantic judgments, include source bodies or orchestrate LLM sessions.

Git tree inventory is independent of Neo4j alias matching. The bounded Git text search is **lexical nomination only**, never independent semantic ground truth. Unsearched or inaccessible systems are reported explicitly. When a graph response is supplied, its candidate-only state and feature revision must match; source object/hash disagreement is reported, not silently reconciled. A graph response page is not treated as a complete graph search if more pages exist.

## Source and access boundaries

- Read committed Git objects at named revisions, not mutable worktree contents.
- Use only a native existing `objective_evidence` implementation from an **exact committed** #50 checkout. Check the implementation file bytes against that commit before importing, and use an existing loopback Bolt tunnel with a READ-access session. No call to the projection building CLI.
- No source bodies or credentials in the output. Sensitive filenames may remain in local source inventory metadata; review outputs before sharing.
- Emit full Git-tree *count* and bounded nominated source pointers. The adapter is not a complete institutional source inventory for external systems.
- Candidate relevance and access classification are only preliminary; metadata does not independently prove an operator can disclose the underlying source.
- Record separate `main_revision` and `feature_revision`; feature code is not promoted release state.

## Outputs

`context-input.json`, `context-manifest.json`, `context-packet.md`, `discovery-coverage.json`, and two pinned revision text files. They are local observational artifacts, not governed facts until admitted through existing SAGE/Git evidence lineage. Stable result identity depends on the same objective, revisions and source observations.

## Limitations and continuation

The packet displays candidate **references**, not authoritative excerpts or independently evaluated context. No semantic completeness guarantee or automatic 9/9 #50 acceptance. Source bodies require an independently bounded, source-authorized extraction step; independent critic and fresh-agent execution are separate objective milestones. Existing GitHub PR context advisory #53 captures scope and uncertainty through the normal PR lifecycle.
