(() => {
  "use strict";

  const state = window.KALAXY3_WORKBENCH_STATE;
  const root = document.getElementById("app");

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) {
      node.textContent = String(text);
    }
    return node;
  }

  function append(parent, ...children) {
    children.filter(Boolean).forEach((child) => parent.appendChild(child));
    return parent;
  }

  function badge(label, kind) {
    return el("span", `badge badge-${kind || "neutral"}`, label);
  }

  function list(items, className = "plain-list") {
    const ul = el("ul", className);
    (items || []).forEach((item) => {
      ul.appendChild(el("li", "", item));
    });
    return ul;
  }

  function titleCase(value) {
    return String(value || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function evidenceDetails(records) {
    const details = el("details", "evidence-details");
    const summary = el(
      "summary",
      "",
      `Inspect evidence (${(records || []).length})`
    );
    details.appendChild(summary);

    (records || []).forEach((record) => {
      const card = el("article", "evidence-card");
      append(
        card,
        badge("Evidence", "evidence"),
        el("h5", "", record.title || record.evidence_ref),
        el("p", "mono evidence-ref", record.evidence_ref),
        el("p", "source-path", record.source_path || "")
      );

      const facts = record.applicable_facts || [];
      if (facts.length) {
        card.appendChild(el("p", "mini-label", "Applicable facts"));
        const factList = el("ul", "fact-list");
        facts.forEach((fact) => {
          factList.appendChild(el("li", "", fact.value || ""));
        });
        card.appendChild(factList);
      }

      const meta = el("div", "meta-row");
      if (record.status) meta.appendChild(badge(record.status, "neutral"));
      if (record.confidence && record.confidence.value) {
        meta.appendChild(
          badge(`confidence: ${record.confidence.value}`, "neutral")
        );
      }
      if (record.recency && record.recency.value) {
        meta.appendChild(
          badge(`recency: ${record.recency.value}`, "neutral")
        );
      }
      card.appendChild(meta);
      details.appendChild(card);
    });

    return details;
  }

  function sectionHeading(kicker, title, description) {
    const block = el("div", "section-heading");
    append(
      block,
      el("p", "eyebrow", kicker),
      el("h2", "", title),
      el("p", "section-description", description)
    );
    return block;
  }

  function renderHero() {
    const section = el("section", "hero panel");
    const objective = state.objective;
    append(
      section,
      el("p", "eyebrow", "Current Architect objective"),
      el("h2", "", objective.statement),
      append(
        el("div", "meta-row"),
        badge("Architect", "architect"),
        badge("read only", "neutral"),
        badge("stakeholder UI proof", "neutral")
      ),
      el(
        "p",
        "supporting-copy",
        "This surface separates accumulated evidence, semantic interpretation, " +
          "new possibilities, uncertainty, and human authority."
      )
    );
    return section;
  }

  function renderLegend() {
    const section = el("section", "legend panel");
    section.appendChild(
      sectionHeading(
        "How to read this",
        "Epistemic identity stays visible",
        "A label tells you what kind of claim you are looking at."
      )
    );
    const grid = el("div", "legend-grid");
    state.epistemic_legend.forEach((item) => {
      const card = el("article", "legend-item");
      append(
        card,
        badge(item.label, item.id),
        el("p", "", item.meaning)
      );
      grid.appendChild(card);
    });
    section.appendChild(grid);
    return section;
  }

  function renderThemes() {
    const section = el("section", "panel");
    section.appendChild(
      sectionHeading(
        "1 / Experience",
        "What can SAGE help me with?",
        "Themes are LLM-derived from a bounded governed experience corpus; " +
          "each one links back to the evidence used."
      )
    );

    const grid = el("div", "card-grid");
    state.experience_themes.forEach((theme) => {
      const card = el("article", "content-card");
      append(
        card,
        append(
          el("div", "card-topline"),
          badge("LLM-derived", "llm-derived")
        ),
        el("h3", "", titleCase(theme.theme)),
        el("p", "lead", theme.what_the_experience_suggests),
        el("p", "mini-label", "Why this theme"),
        el("p", "", theme.why_this_theme)
      );

      if ((theme.limits || []).length) {
        card.appendChild(el("p", "mini-label", "Limits"));
        card.appendChild(list(theme.limits));
      }

      card.appendChild(evidenceDetails(theme.evidence || []));
      grid.appendChild(card);
    });
    section.appendChild(grid);
    return section;
  }

  function relationshipBadge(value) {
    const label = titleCase(value);
    let kind = "neutral";
    if (value === "directly_relevant") kind = "direct";
    if (value === "analogous") kind = "analogous";
    if (value === "contradictory") kind = "contradictory";
    return badge(label, kind);
  }

  function renderApplicability() {
    const section = el("section", "panel");
    section.appendChild(
      sectionHeading(
        "2 / Intent",
        "Given this objective, what matters?",
        "Semantic transfer judgments explain relevance, assumptions, unknowns, " +
          "and implications without turning them into demonstrated facts."
      )
    );

    const grid = el("div", "card-grid");
    state.intent_applicability.forEach((item) => {
      const card = el("article", "content-card");
      append(
        card,
        append(
          el("div", "card-topline"),
          badge("LLM-derived", "llm-derived"),
          relationshipBadge(item.semantic_relationship)
        ),
        el("h3", "", titleCase(item.intent_area)),
        el("p", "lead", item.why),
        el("p", "mini-label", "Implication"),
        el("p", "", item.implication)
      );

      if ((item.assumptions || []).length) {
        card.appendChild(el("p", "mini-label", "Assumptions"));
        card.appendChild(list(item.assumptions));
      }

      if ((item.unknowns || []).length) {
        card.appendChild(el("p", "mini-label", "Still unknown"));
        card.appendChild(list(item.unknowns, "unknown-list"));
      }

      card.appendChild(
        append(
          el("div", "authority-strip"),
          badge("Architect judgment required", "architect"),
          el(
            "span",
            "",
            "Transfer is a human decision, not an automatic promotion."
          )
        )
      );
      card.appendChild(evidenceDetails(item.evidence || []));
      grid.appendChild(card);
    });
    section.appendChild(grid);
    return section;
  }

  function renderHumanJudgment() {
    const section = el("section", "panel");
    section.appendChild(
      sectionHeading(
        "3 / Participation",
        "Where is my judgment valuable?",
        "SAGE exposes choices and the LLM can propose beyond experience; " +
          "neither silently becomes authority."
      )
    );

    const columns = el("div", "decision-grid");

    const decisions = el("div", "decision-column");
    append(
      decisions,
      append(
        el("div", "column-heading"),
        badge("Architect", "architect"),
        el("h3", "", "Decisions that remain yours")
      )
    );
    state.architect_decisions.forEach((item) => {
      const card = el("article", "decision-card");
      append(
        card,
        el("p", "lead", item.decision),
        badge(titleCase(item.decision_type), "neutral")
      );
      decisions.appendChild(card);
    });

    const innovations = el("div", "decision-column");
    append(
      innovations,
      append(
        el("div", "column-heading"),
        badge("LLM-proposed", "llm-proposed"),
        el("h3", "", "Possibilities beyond prior experience")
      )
    );
    state.innovation_beyond_experience.forEach((item) => {
      const card = el("article", "decision-card");
      append(
        card,
        el("p", "lead", item.proposal),
        el("p", "", item.why),
        badge(
          `experience dependency: ${item.experience_dependency}`,
          "neutral"
        )
      );
      innovations.appendChild(card);
    });

    append(columns, decisions, innovations);
    section.appendChild(columns);
    return section;
  }

  function renderUnknowns() {
    const section = el("section", "panel uncertainty-panel");
    section.appendChild(
      sectionHeading(
        "Uncertainty",
        "What we should not pretend to know",
        "Unknowns and unavailable evidence stay visible instead of being " +
          "filled in by inference."
      )
    );

    section.appendChild(list(state.unknowns, "unknown-list"));

    if ((state.evidence_availability || []).length) {
      const availability = el("div", "availability-grid");
      state.evidence_availability.forEach((item) => {
        const card = el("article", "availability-card");
        append(
          card,
          el("p", "mini-label", titleCase(item.source_type)),
          badge(titleCase(item.availability), "neutral")
        );
        availability.appendChild(card);
      });
      section.appendChild(availability);
    }
    return section;
  }

  function renderProvenance() {
    const section = el("section", "provenance panel");
    section.appendChild(
      sectionHeading(
        "Provenance",
        "Why this surface is inspectable",
        "The workbench is a presentation of persisted projections, not a new " +
          "source of truth."
      )
    );

    const grid = el("div", "provenance-grid");
    const values = [
      ["Corpus SHA-256", state.provenance.semantic_corpus_sha256],
      [
        "Evidence citations resolved",
        state.provenance.evidence_citations_resolved,
      ],
      [
        "SAGE claims semantic truth",
        state.provenance.semantic_truth_validated_by_sage,
      ],
      ["Authority", state.provenance.architect_authority],
    ];

    values.forEach(([label, value]) => {
      const card = el("article", "provenance-item");
      append(
        card,
        el("p", "mini-label", label),
        el("p", label === "Corpus SHA-256" ? "mono" : "", value)
      );
      grid.appendChild(card);
    });
    section.appendChild(grid);
    return section;
  }

  function render() {
    if (!state || state.interaction_mode !== "read_only") {
      root.appendChild(
        el(
          "p",
          "fatal",
          "Workbench state is unavailable or violates the read-only contract."
        )
      );
      return;
    }

    append(
      root,
      renderHero(),
      renderLegend(),
      renderThemes(),
      renderApplicability(),
      renderHumanJudgment(),
      renderUnknowns(),
      renderProvenance()
    );
  }

  render();
})();
