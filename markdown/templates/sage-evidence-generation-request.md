# Canonical SAGE working-session evidence request

Use this exact request after a Kalaxy3 working session:

> Generate the SAGE evidence package for the most recent Kalaxy3 working
> session using the repository SAGE evidence-record standard, evidence-record
> template, and evidence-publication process. Include all available terminal
> and repository evidence, the final accepted state, failed attempts, decision
> rationale, limitations, evidence gaps, rollback and rebuild guidance,
> idempotency evidence, and security review. Produce one valid ZIP package with
> `sage-package.json` and `payload/`. Return the package and only the standard
> check and publication commands; do not invent a different Git workflow.

The expected response contains:

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

The evidence generator must not provide an ad hoc sequence of `unzip`, `git
add`, `git commit`, `pull`, or `push` commands. Those operations belong to the
repository publication script.
