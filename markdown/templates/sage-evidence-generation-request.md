# Canonical SAGE working-session evidence request

Use this exact request after a Kalaxy3 working session:

> Generate the SAGE evidence package for the most recent Kalaxy3 working
> session using the repository SAGE evidence-record standard, canonical
> metadata contract, evidence-record template, evidence-publication process,
> and evidence-navigation compatibility rules. Use schema 1.2. Populate every
> canonical front-matter field in exact order, including formal title,
> navigation title, navigation section, navigation order, summary, and primary
> subject. Generate the exact Record metadata table from front matter, include
> an explicit `[TOC]`, and keep the Five Ws consistent with canonical metadata.
> Include all available terminal and repository evidence, final state, failed
> attempts, rationale, limitations, gaps, rollback, rebuild, idempotency,
> security review, and revalidation. Preserve historical evidence through the
> existing catalog and legacy registry rather than rewriting or excluding it.
> Produce one valid ZIP with `sage-package.json` and `payload/`. Return the
> package and only the standard check and publication commands. Do not invent
> another metadata format, navigation format, or Git workflow.

Expected response:

1. one ZIP package;
2. one validation command:

   ```bash
   python3 scripts/sage/sage-publish.py check ~/Downloads/<package>.zip
   ```

3. one publication command:

   ```bash
   python3 scripts/sage/sage-publish.py publish \
     ~/Downloads/<package>.zip \
     --push
   ```

The generator must not provide an ad hoc static header, manual catalog edit,
`unzip`, `git add`, `git commit`, `pull`, or `push` workflow. Canonical metadata,
legacy preservation, navigation reconciliation, and Git publication belong to
the repository contracts and publisher.
