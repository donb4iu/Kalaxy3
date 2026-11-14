# Issue #50 — blinded independent semantic evidence review

**Purpose:** DOD-06 measurement preparation, not evidence maturity, qualification, architectural acceptance, or projection promotion.

## Input authority and independence

Review packets enumerate source–concept pairs from the exact committed Kalaxy3 Git tree and current committed `sage-semantic-concepts.json`. The operator tool samples matcher-nominated and non-nominated pairs, **without disclosing matcher predictions to reviewers**. Reviewers must judge source content and contextual relevance independently, using their own authorized access to the exact Git revision; output includes only source identities/digests, not raw source bodies. The sample intentionally oversamples nominations; it does **not** estimate corpus-wide precision or recall.

The independent reviewer must not use the predicted candidate list as the answer key. Fill `labels-template.json` with the reviewer's name, an accountable annotation reference, each `verdict` (`relevant`, `irrelevant`, or `uncertain`), and a substantive `basis`. All sampled pairs must be accounted for; unresolved cases may be `uncertain`, not silently dropped or counted as irrelevant. The review selection and labels must be preserved as separate evidence. No self-certification of reviewer independence is performed.

## Version identity and failure behavior

`review-packet.json` binds Git revision, projection fingerprint, independent source SHA-256, Git object identity, sampled pairs and complete scope denominators. The filled labels must match the issued packet and entire case set. New commits, changed model inputs, removed cases, duplicate cases or changed packet identity fail closed. Output remains local to the operator's Downloads evidence directory and must not be committed automatically.

If `sage-semantic-concepts.json` does not exist at the committed source revision, return `not_evaluated` with exact source count. Do not import another branch's model, infer one from file names, or claim negative evidence. Source scope and externally owned proof remain authoritative in their respective native systems.

## Interpretation and next acceptance boundary

Measure only sampled-pair precision, recall, false positives, misses and unresolved judgments. Preserve both missed lexical/paraphrase evidence and irrelevant lexical matches. SAGE must independently validate concept/solution breadth and query-level paraphrase recall; this sampling workflow **does not** satisfy those tests by itself. Architect retains final threshold selection and DoD acceptance; a qualified promotion requires the separately governed SAGE promotion and authority contracts.

No production deployment, Cloudflare/MetalLB modification, Git promotion, credential creation or graph activation is authorized here.
