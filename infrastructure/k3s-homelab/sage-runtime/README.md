# Kalaxy3 Architecture Helper — direct repair

The Architect authorized restoration of productive Kalaxy3 work. This package reuses
LangGraph `StateGraph`/`SqliteSaver`, LangChain `InMemoryVectorStore`/`OllamaEmbeddings`,
existing Ollama/K3s/Longhorn, and the repository-owned
`scripts/sage/sage-request-execute.py`. It does not attempt to repair the obsolete
`resume_fresh_role_correction` patch, install HashiCorp Vault, or create another
SAGE coordinator.

## Run

Extract `sage-architecture-helper-repair-20261024.zip` into Downloads and run
`bash ~/Downloads/sage-architecture-helper-repair/run.command`.

The command tests the package, copies it to the existing Kalaxy3 feature branch,
commits/pushes only the new runtime subtree, deploys it using the existing K3s
context, and runs an actual retrieval + Ollama architecture question in-cluster.
It leaves the previously qualified six-file local source changes untouched.
A single K3s cluster is reused; no Docker on the workstation.

## Functional interfaces

- `POST /v1/architecture/ask`: produces cited, **read-only** Architecture Helper
  answers using evidence retrieved from a pinned main-line Git commit. This
  endpoint does not require an accepted SAGE action, because read-only analysis
  must not manufacture acceptance or execution authority.
- `POST /v1/proposals`: stores at most 6MiB in content-addressed operational
  storage; the response is `stored-unverified`. The governed executor must still
  validate the exact SAGE proposal manifest and accepted objective.
- `POST /v1/objectives/{accepted_action}/advise`: uses the reference checkpointed
  Engineering/Referee graph and auto-correction. With an explicit
  `execution_submission` (exact `revision`, `head`, `branch`, and `package_id`),
  it verifies accepted action authority, clones a matching isolated feature
  checkout, and invokes the existing request-execution CLI. The success state
  is **governed Git boundary pending**, never finished objective or merge.

Use `bash ~/Downloads/sage-architecture-helper-repair/ask.command "question"`
to ask from a workstation with access to the K3s context. The command uses
`kubectl port-forward` and existing API authorization.

## Persistence and safety

Git remains the authority for objectives, accepted decisions, and versioned
source evidence. LangGraph SQLite and the LangChain vector store are
reconstructable runtime projections, hosted on existing Longhorn storage.
An ephemeral user/API token is provisioned as a Kubernetes Secret when the
SAGE service Secret is absent; it does **not** assert HashiCorp Vault or
Ansible-Vault provenance. This runtime bootstrap credential should subsequently
be incorporated into existing Ansible Vault deployment management.

The actual CLI still generates a governed operator Git proposal; the adapter
will not bypass that contract or assert automatic Git promotion. No LLM owns
Kubernetes or Git mutation credentials. Neither retrieval success nor source
validation proves complete Architecture Helper execution.

## Tests

Local Python standard-library tests check exact Git source retrieval, clean
feature workspaces, original request binding, tamper rejection, and evidence
citations. The real LangGraph checkpoint test is run in cluster (and skipped
locally if libraries are absent). In-cluster `service.selfcheck` and
`service.probe` verify the actual inference and retrieval configuration.

If deployment cannot reach Ollama, fails Kubernetes permissions, or cannot
retrieve authoritative evidence, it stops with the actual cause and keeps the
existing feature source and evidence intact.
