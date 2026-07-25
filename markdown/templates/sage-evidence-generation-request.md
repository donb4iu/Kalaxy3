# Canonical SAGE working-session evidence request

Use this exact request after a Kalaxy3 working session:

> Generate the SAGE evidence package for the most recent Kalaxy3 working
> session using the repository SAGE evidence-record standard, canonical
> metadata contract, evidence-record template, and evidence-publication
> process. Use schema 1.1. Populate every canonical front-matter field in exact
> order; distinguish work completion, evidence collection, record timestamps,
> local timezone, and system timestamp timezone; normalize nodes and addresses,
> endpoints, and component versions; generate the exact Record metadata table
> from front matter; and keep the Five Ws consistent with it. Include all
> available terminal and repository evidence, final state, failed attempts,
> rationale, limitations, evidence gaps, rollback, rebuild, idempotency, and
> security review. Produce one valid ZIP with `sage-package.json` and
> `payload/`. Return the package and only the standard check and publication
> commands. Do not invent another metadata format or Git workflow.

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

The generator must not provide an ad hoc static header, `unzip`, `git add`,
`git commit`, `pull`, or `push` workflow. Canonical metadata and Git publication
belong to the repository contracts and publisher.
