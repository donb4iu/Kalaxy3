(() => {
  "use strict";

  const workbench = window.KALAXY3_WORKBENCH_STATE;
  const graph = window.KALAXY3_EXPERIENCE_GRAPH;
  const narrationRoot = window.KALAXY3_NARRATION || { entries: {} };
  const narration = narrationRoot.entries || {};
  const root = document.getElementById("app");

  const byId = new Map((graph.entities || []).map((item) => [item.id, item]));

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

  function badge(label, kind = "neutral") {
    return el("span", `badge badge-${kind}`, label);
  }

  function titleCase(value) {
    return String(value || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function list(items, className = "plain-list") {
    const ul = el("ul", className);
    (items || []).forEach((item) => ul.appendChild(el("li", "", item)));
    return ul;
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

  function homePanel(href, title, body, meta) {
    const link = el("a", "home-panel");
    link.href = href;
    append(
      link,
      el("p", "mini-label", meta),
      el("h3", "", title),
      el("p", "", body),
      el("span", "panel-link", "Explore →")
    );
    return link;
  }

  function renderHome() {
    const section = el("section", "panel");
    section.id = "home";
    section.appendChild(
      sectionHeading(
        "Start anywhere",
        "Explore SAGE through outcomes and accumulated experience",
        "These are peer entry points into the same governed relationship " +
          "network. There is no required reading order."
      )
    );

    const grid = el("div", "home-grid");
    append(
      grid,
      homePanel(
        "#experiences",
        "Objectives & experiences",
        "What has been attempted or accomplished, what it cost to discover, " +
          "what was learned, and what should be reusable next time.",
        "What SAGE has helped accomplish and learn"
      ),
      homePanel(
        "#capabilities",
        "Capabilities",
        "What kinds of problems SAGE has accumulated useful experience " +
          "addressing and where those capabilities came from.",
        "What SAGE can help with"
      ),
      homePanel(
        "#current",
        "Current objective",
        "Which prior experience appears relevant now, what remains uncertain, " +
          "and what new possibilities exist beyond experience.",
        "What matters right now"
      ),
      homePanel(
        "#judgment",
        "Human judgment",
        "Consequential choices, their evidence, downstream implications, " +
          "debt, and whether later learning changed the assessment.",
        "Where judgment shaped outcomes"
      ),
      homePanel(
        "#interaction",
        "Role interaction",
        "See how Architect intent, LLM innovation, SAGE reconciliation, " +
          "execution, evidence and learning combined to produce an outcome.",
        "How the work came together"
      )
    );
    section.appendChild(grid);

    const searchWrap = el("div", "search-wrap");
    const label = el("label", "mini-label", "Find anything in experience");
    label.htmlFor = "global-search";
    const input = el("input", "search-input");
    input.id = "global-search";
    input.type = "search";
    input.placeholder = "Search IDs, titles, types, status, source paths…";
    input.autocomplete = "off";
    append(searchWrap, label, input);
    section.appendChild(searchWrap);

    input.addEventListener("input", () => {
      const term = input.value.trim().toLowerCase();
      document.querySelectorAll("[data-search-text]").forEach((node) => {
        const haystack = node.getAttribute("data-search-text") || "";
        node.hidden = term !== "" && !haystack.includes(term);
      });
    });

    return section;
  }

  function standingBadge(standing) {
    const state = standing?.state || "unknown";
    let kind = "neutral";
    if (["superseded", "contradicted", "invalidated"].includes(state)) {
      kind = "contradictory";
    }
    if (["context_limited", "potentially_stale"].includes(state)) {
      kind = "warning";
    }
    return badge(titleCase(state), kind);
  }

  function narrationBlock(entity) {
    const note = narration[entity.id];
    if (!note) {
      return append(
        el("div", "raw-mode-note"),
        badge("Raw governed view", "sage-derived"),
        el(
          "p",
          "",
          "No optional human-language narration is attached to this entity. " +
            "The relationships and metadata below remain fully inspectable."
        )
      );
    }

    const block = el("div", "narration-block");
    append(
      block,
      badge("Optional LLM narration", "llm-derived"),
      el("p", "mini-label", "What this means"),
      el("p", "lead", note.what_this_means),
      el("p", "mini-label", "What it enables"),
      el("p", "", note.what_it_enables),
      el("p", "mini-label", "Why it matters"),
      el("p", "", note.why_it_matters)
    );

    if (note.historical_effort_context) {
      append(
        block,
        el("p", "mini-label", "Historical effort"),
        el("p", "", note.historical_effort_context)
      );
    }
    if (note.reusable_value_created) {
      append(
        block,
        el("p", "mini-label", "Reusable value created"),
        el("p", "", note.reusable_value_created)
      );
    }
    if (note.expected_repeat_effect) {
      const repeat = el("div", "repeat-effect");
      append(
        repeat,
        badge("Predicted repeat effect", "llm-proposed"),
        el("p", "", note.expected_repeat_effect)
      );
      block.appendChild(repeat);
    }
    if ((note.limits || []).length) {
      block.appendChild(el("p", "mini-label", "Limits"));
      block.appendChild(list(note.limits));
    }
    return block;
  }

  function pathSignals(entity) {
    const entries = Object.entries(entity.path_signals || {});
    const box = el("div", "signals");
    append(
      box,
      el("p", "mini-label", "Observed path signals"),
      el(
        "p",
        "signal-disclaimer",
        "Historical linked-record counts. They are not a future effort estimate."
      )
    );
    if (!entries.length) {
      box.appendChild(el("p", "muted", "No linked path signals found."));
      return box;
    }
    const row = el("div", "signal-row");
    entries.forEach(([kind, count]) => {
      row.appendChild(badge(`${titleCase(kind)}: ${count}`, "neutral"));
    });
    box.appendChild(row);
    return box;
  }

  function roleInteractionBlock(entity) {
    const block = el("div", "role-block");
    append(
      block,
      el("p", "mini-label", "How this came together"),
      el(
        "p",
        "muted",
        "Only explicit role provenance is shown. Missing attribution remains unknown."
      )
    );

    const roles = entity.role_interaction || [];
    if (!roles.length) {
      block.appendChild(
        el("p", "muted", "No explicit role attribution found for this episode.")
      );
      return block;
    }

    const lane = el("div", "role-lane");
    roles.forEach((item) => {
      const card = el("article", "role-card");
      let kind = "neutral";
      if (item.role === "Architect") kind = "architect";
      if (item.role === "LLM") kind = "llm-proposed";
      if (item.role === "SAGE") kind = "sage-derived";
      append(
        card,
        badge(item.role, kind),
        el("p", "", item.title),
        el("a", "mono tiny role-link", item.entity_id)
      );
      card.querySelector("a").href =
        `#entity-${encodeURIComponent(item.entity_id)}`;
      lane.appendChild(card);
    });
    block.appendChild(lane);
    return block;
  }

  function rawFields(entity) {
    const details = el("details", "raw-details");
    details.appendChild(el("summary", "", "Inspect governed metadata"));
    const table = el("dl", "metadata-grid");
    Object.entries(entity.raw_fields || {}).forEach(([key, value]) => {
      table.appendChild(el("dt", "", titleCase(key)));
      table.appendChild(
        el(
          "dd",
          "",
          Array.isArray(value) ? value.join(", ") : String(value)
        )
      );
    });
    if (!Object.keys(entity.raw_fields || {}).length) {
      details.appendChild(el("p", "muted", "No compact scalar metadata."));
    } else {
      details.appendChild(table);
    }
    return details;
  }

  function entityLink(entity, relation) {
    const link = el("a", "relation-link");
    link.href = `#entity-${encodeURIComponent(entity.id)}`;
    append(
      link,
      badge(titleCase(relation), "neutral"),
      el("span", "", entity.title || entity.id),
      el("span", "mono tiny", entity.id)
    );
    return link;
  }

  function relationList(entity, direction) {
    const edges = entity[direction] || [];
    const wrap = el("div", "relation-group");
    wrap.appendChild(
      el(
        "p",
        "mini-label",
        direction === "incoming"
          ? "What points here / downstream use"
          : "Where this points / upstream context"
      )
    );
    if (!edges.length) {
      wrap.appendChild(el("p", "muted", "No explicit relationships found."));
      return wrap;
    }

    const semantic = edges.filter((edge) => edge.semantic);
    const generic = edges.filter((edge) => !edge.semantic);

    if (semantic.length) {
      const bucket = el("div", "relation-bucket");
      bucket.appendChild(el("p", "relation-label", "Semantic relationships"));
      semantic.slice(0, 30).forEach((edge) => {
        const targetId = direction === "incoming" ? edge.source : edge.target;
        const target = byId.get(targetId);
        if (target) bucket.appendChild(entityLink(target, edge.relation));
      });
      wrap.appendChild(bucket);
    }

    if (generic.length) {
      const details = el("details", "reference-details");
      details.appendChild(
        el("summary", "", `Other explicit references (${generic.length})`)
      );
      generic.slice(0, 50).forEach((edge) => {
        const targetId = direction === "incoming" ? edge.source : edge.target;
        const target = byId.get(targetId);
        if (target) details.appendChild(entityLink(target, "reference"));
      });
      wrap.appendChild(details);
    }
    return wrap;
  }

  function entityCard(entity) {
    const card = el("article", "entity-card");
    card.id = `entity-${entity.id}`;
    card.setAttribute(
      "data-search-text",
      [
        entity.id,
        entity.title,
        entity.entity_type,
        entity.status,
        ...(entity.source_paths || []),
      ]
        .join(" ")
        .toLowerCase()
    );

    append(
      card,
      append(
        el("div", "card-topline"),
        badge(titleCase(entity.entity_type), "sage-derived"),
        standingBadge(entity.current_standing),
        narration[entity.id]
          ? badge("Explained", "llm-derived")
          : badge("Raw", "neutral")
      ),
      el("h3", "", entity.title),
      el("p", "mono entity-id", entity.id),
      narrationBlock(entity),
      entity.is_episode ? roleInteractionBlock(entity) : null,
      pathSignals(entity)
    );

    const standing = el("div", "standing-note");
    append(
      standing,
      el("p", "mini-label", "Current standing"),
      el("p", "", titleCase(entity.current_standing?.state || "unknown")),
      el("p", "muted", entity.current_standing?.basis || "")
    );
    card.appendChild(standing);

    const relations = el("div", "relation-columns");
    append(
      relations,
      relationList(entity, "outgoing"),
      relationList(entity, "incoming")
    );
    card.appendChild(relations);

    const sources = el("details", "raw-details");
    sources.appendChild(
      el("summary", "", `Source provenance (${entity.source_paths.length})`)
    );
    sources.appendChild(list(entity.source_paths, "source-list"));
    card.appendChild(sources);
    card.appendChild(rawFields(entity));
    return card;
  }

  function paginatedEntities(items, sectionId, batch = 20) {
    const wrap = el("div", "entity-list");
    let visible = batch;

    function draw() {
      wrap.textContent = "";
      items.slice(0, visible).forEach((item) => {
        wrap.appendChild(entityCard(item));
      });
      if (visible < items.length) {
        const button = el(
          "button",
          "show-more",
          `Show ${Math.min(batch, items.length - visible)} more`
        );
        button.type = "button";
        button.addEventListener("click", () => {
          visible += batch;
          draw();
          document.getElementById(sectionId)?.scrollIntoView({
            block: "start",
          });
        });
        wrap.appendChild(button);
      }
    }

    draw();
    return wrap;
  }

  function entitySection(id, kicker, title, description, items) {
    const section = el("section", "panel");
    section.id = id;
    section.appendChild(sectionHeading(kicker, title, description));
    section.appendChild(
      el("p", "section-count", `${items.length} discovered`)
    );
    section.appendChild(paginatedEntities(items, id));
    return section;
  }

  function renderCurrentObjective() {
    const section = el("section", "panel");
    section.id = "current";
    section.appendChild(
      sectionHeading(
        "Current objective",
        "What matters right now",
        "Architect intent defines the desired future state. Relevant experience " +
          "and LLM innovation inform how we might get there."
      )
    );

    const objective = workbench.objective;
    append(
      section,
      badge("Architect intent", "architect"),
      el("h3", "current-objective", objective.statement)
    );

    const grid = el("div", "current-grid");
    (workbench.intent_applicability || []).forEach((item) => {
      const card = el("article", "summary-card");
      append(
        card,
        badge("LLM-derived experience interpretation", "llm-derived"),
        el("h4", "", titleCase(item.intent_area)),
        badge(titleCase(item.semantic_relationship), "neutral"),
        el("p", "", item.why),
        el("p", "mini-label", "Implication"),
        el("p", "", item.implication)
      );
      if ((item.unknowns || []).length) {
        card.appendChild(el("p", "mini-label", "Unknowns"));
        card.appendChild(list(item.unknowns, "unknown-list"));
      }
      grid.appendChild(card);
    });
    section.appendChild(grid);

    const innovation = el("div", "innovation-zone");
    append(
      innovation,
      el("p", "mini-label", "LLM innovation beyond prior experience"),
      el(
        "p",
        "muted",
        "These are proposed possibilities, not SAGE facts or Architect decisions."
      )
    );
    const proposals = el("div", "current-grid");
    (workbench.innovation_beyond_experience || []).forEach((item) => {
      const card = el("article", "summary-card");
      append(
        card,
        badge("LLM-proposed", "llm-proposed"),
        el("h4", "", item.proposal),
        el("p", "", item.why)
      );
      proposals.appendChild(card);
    });
    innovation.appendChild(proposals);
    section.appendChild(innovation);

    return section;
  }

  function renderJudgment(decisionEntities) {
    const section = el("section", "panel");
    section.id = "judgment";
    section.appendChild(
      sectionHeading(
        "Human judgment",
        "Where judgment shaped outcomes",
        "Human authority is visible without assuming the judgment was always " +
          "correct. Downstream relationships and debt remain inspectable when " +
          "the governed records preserve them."
      )
    );

    const current = el("div", "decision-grid");
    (workbench.architect_decisions || []).forEach((item) => {
      const card = el("article", "summary-card");
      append(
        card,
        badge("Architect", "architect"),
        el("h4", "", item.decision),
        badge(titleCase(item.decision_type), "neutral")
      );
      current.appendChild(card);
    });
    section.appendChild(current);

    if (decisionEntities.length) {
      section.appendChild(
        sectionHeading(
          "Repository decision lineage",
          "Governed decision records",
          "Raw decision records can be investigated even when no narration has " +
            "been generated."
        )
      );
      section.appendChild(paginatedEntities(decisionEntities, "judgment", 10));
    }
    return section;
  }

  function renderInteraction(episodes) {
    const section = el("section", "panel");
    section.id = "interaction";
    section.appendChild(
      sectionHeading(
        "Role interaction",
        "How the work came together",
        "Architect intent, LLM innovation, SAGE reconciliation, execution and " +
          "learning are different contributions. This view shows only role " +
          "attribution preserved by provenance."
      )
    );

    const model = el("div", "interaction-model");
    [
      ["Architect", "Defines intent, end state, constraints, trade-offs and consequential approvals.", "architect"],
      ["LLM", "Widens the solution space with alternatives, architecture, critique, experiments and innovation.", "llm-proposed"],
      ["SAGE", "Reconciles proposals with evidence, experience, authority, guardrails, unknowns and executable capability.", "sage-derived"],
      ["Executor / external systems", "Perform governed work and emit observable results and receipts.", "neutral"],
      ["Learning", "Compares expectation with outcome and records reusable insight, debt, staleness and next-time effects.", "evidence"]
    ].forEach(([role, body, kind]) => {
      const card = el("article", "role-model-card");
      append(card, badge(role, kind), el("p", "", body));
      model.appendChild(card);
    });
    section.appendChild(model);

    const attributed = episodes.filter(
      (item) => (item.role_interaction || []).length
    );
    section.appendChild(
      sectionHeading(
        "Recorded interaction",
        "Episodes with explicit role provenance",
        `${attributed.length} episodes currently expose at least one explicit role attribution.`
      )
    );
    section.appendChild(paginatedEntities(attributed, "interaction", 10));
    return section;
  }

  function render() {
    if (!workbench || !graph || workbench.interaction_mode !== "read_only") {
      root.appendChild(
        el(
          "p",
          "fatal",
          "Workbench state is unavailable or violates the read-only contract."
        )
      );
      return;
    }

    const entities = graph.entities || [];
    const episodes = entities.filter((item) => item.is_episode);
    const capabilities = entities.filter(
      (item) => item.entity_type === "capability"
    );
    const decisions = entities.filter(
      (item) => item.entity_type === "decision"
    );
    const learning = entities.filter((item) =>
      ["causal_insight", "lesson", "failure", "review", "candidate"].includes(
        item.entity_type
      )
    );
    const evidence = entities.filter(
      (item) => item.entity_type === "evidence"
    );

    append(
      root,
      renderHome(),
      entitySection(
        "experiences",
        "Objectives & experiences",
        "What SAGE has helped accomplish and learn",
        "Every discovered governed objective/episode is available in raw form. " +
          "Selected entities may add optional plain-English narration without " +
          "changing the canonical record.",
        episodes
      ),
      entitySection(
        "capabilities",
        "Capabilities",
        "What SAGE can help with",
        "Browse capability records and follow their links back to the work that " +
          "created, reused or referenced them.",
        capabilities
      ),
      renderCurrentObjective(),
      renderJudgment(decisions),
      renderInteraction(episodes),
      entitySection(
        "learning",
        "Learning",
        "Causal insights, lessons, failures and reviews",
        "Incomplete or partially supported learning remains visible. Explicit " +
          "supersession, contradiction and later reuse use the same relationship model.",
        learning
      ),
      entitySection(
        "evidence",
        "Evidence multiplier",
        "Evidence and where it has been used",
        "Each record can be investigated in both directions: what it references " +
          "and what later records point back to it.",
        evidence
      )
    );
  }

  render();
})();
