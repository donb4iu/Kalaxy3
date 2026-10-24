"""Authenticated SAGE cognitive workbench service for the Kalaxy3 cluster."""

from __future__ import annotations

import hashlib
import hmac
import zipfile
import os
import tempfile
import subprocess
import threading
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from .context import ContextError, clone_repository, compile_context, pin_revision
from .handoff import HandoffError, execute_qualified, prepare_workspace
from .architect import build_architect_graph, make_ollama_adapter
from .evidence import compile_evidence
from .roles import invoke_ollama
from .workflow import build_graph, stable_digest


app = FastAPI(title="Kalaxy3 SAGE shared cognitive runtime", version="0.1.0")
_lock = threading.Lock()


class AdvisoryRequest(BaseModel):
    """A bounded workbench question under an already accepted action."""

    question: str = Field(min_length=8, max_length=4000)
    revision: str | None = Field(default=None, min_length=40, max_length=40)
    execution_submission: dict[str, str] | None = None


def require_token(authorization: str | None = Header(default=None)) -> None:
    """Enforce a Kubernetes Secret-sourced API token on private endpoints.

    Args:
        authorization: HTTP Authorization header.
    """
    secret = os.environ.get("SAGE_API_TOKEN", "")
    if not secret or not authorization or not hmac.compare_digest(
        authorization, f"Bearer {secret}",
    ):
        raise HTTPException(status_code=401, detail="unauthorized")


def read_context(action_id: str, revision: str | None = None,
                 question: str = "") -> dict[str, Any]:
    """Build context exclusively from a temporary Git clone.

    Args:
        action_id: Exact accepted SAGE action identifier.
        revision: Optional historical Git commit for exact restoration.
        question: Specific task for semantic evidence retrieval.
    """
    url = os.environ["SAGE_REPO_URL"]
    with tempfile.TemporaryDirectory(prefix="sage-repository-") as tmp:
        repo = Path(tmp) / "repo"
        head = clone_repository(url, repo)
        selected = pin_revision(repo, revision) if revision else head
        context = compile_context(repo, selected, action_id)
        context["evidence"] = compile_evidence(
            repo, selected, f"{context['objective']} {question}",
            os.environ["SAGE_OLLAMA_URL"],
            os.environ["SAGE_OLLAMA_EMBED_MODEL"],
        )
        for record in context["evidence"]["retrieved_sources"]:
            context["source_sha256"][record["path"]] = record["sha256"]
        return context


def call_role(role: str, envelope: dict[str, Any]) -> dict[str, Any]:
    """Invoke the configured Ollama model using an isolated role instruction.

    Args:
        role: The assigned RACI role.
        envelope: Shared objective, question, and bounded role input.
    """
    systems = {
        "engineering": (
            "You are SAGE Engineering. Prioritize the accepted objective and its "
            "mandatory constraints. Use only cited Git context. Return JSON "
            "with keys proposal (nonempty string) and evidence_paths (list). "
            "Suggest work, but do not claim implementation or approval."),
        "referee": (
            "You are the independent SAGE Referee. Evaluate objective fidelity "
            "and mandatory constraints, not preferences. Return JSON with "
            "verdict 'allow' or 'correct' and findings list. For corrections, "
            "include source_path and source_sha256 matching provided context, "
            "criterion verbatim from objective acceptance_criteria, and a "
            "concrete invariant. Unsupported objections recuse. "
            "Do not pretend to run tests or grant execution authority."),
    }
    if role not in systems:
        raise ValueError("unknown role")
    return invoke_ollama(
        os.environ["SAGE_OLLAMA_URL"], os.environ["SAGE_OLLAMA_MODEL"],
        systems[role], envelope,
    )


def resolve_runner(submission: dict[str, str] | None) -> Any:
    """Resolve an independently bound Git checkout for the governed adapter.

    Args:
        submission: Explicit immutable proposal and Git revision identity.
    """
    if not submission:
        return None
    required = ("SAGE_EXECUTION_WORKSPACES", "SAGE_EXECUTION_PROPOSALS")
    if not all(os.environ.get(key) for key in required):
        raise HTTPException(status_code=409, detail="execution runtime not configured")
    try:
        workspace = prepare_workspace(
            Path(os.environ["SAGE_EXECUTION_WORKSPACES"]),
            os.environ["SAGE_REPO_URL"], submission,
        )
    except (HandoffError, OSError, subprocess.CalledProcessError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    def runner(state: dict[str, Any]) -> dict[str, Any]:
        """Delegate verified work to the repository's existing SAGE executor."""
        return execute_qualified(
            state, repo=workspace,
            proposals=Path(os.environ["SAGE_EXECUTION_PROPOSALS"]),
        )

    return runner


@app.get("/healthz")
def health() -> dict[str, str]:
    """Return process health; this is not objective acceptance evidence."""
    return {"status": "running"}


@app.get("/v1/objectives/{action_id}/context", dependencies=[Depends(require_token)])
def objective_context(action_id: str, revision: str | None = None) -> dict[str, Any]:
    """Return the accepted objective and its pinned Git provenance.

    Args:
        action_id: Exact repository action identifier.
        revision: Optional full Git SHA for time travel.
    """
    try:
        context = read_context(action_id, revision)
        return {key: context[key] for key in (
            "objective_id", "revision", "objective", "acceptance_criteria",
            "source_sha256", "evidence")}
    except (ContextError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/objectives/{action_id}/advise", dependencies=[Depends(require_token)])
def advise(action_id: str, request: AdvisoryRequest) -> dict[str, Any]:
    """Resume one bounded, checkpointed RACI evaluation under a Git action.

    Args:
        action_id: Exact accepted action ID.
        request: Architect workbench question.
    """
    from langgraph.checkpoint.sqlite import SqliteSaver

    try:
        context = read_context(action_id, request.revision, request.question)
    except (ContextError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    initial = {"objective_id": action_id, "revision": context["revision"],
               "context": context, "question": request.question, "attempts": 0,
               "execution_submission": request.execution_submission}
    thread_id = stable_digest({"execution_submission": request.execution_submission,
                               "objective_id": action_id,
                               "revision": context["revision"],
                               "question": request.question,
                               "evidence": context["evidence"]["manifest_sha256"]})
    config = {"configurable": {"thread_id": thread_id}}
    db_path = os.environ.get("SAGE_CHECKPOINT_DB", "/var/lib/sage/checkpoints.sqlite")
    runner = resolve_runner(request.execution_submission)
    with _lock, SqliteSaver.from_conn_string(db_path) as saver:
        graph = build_graph(call_role, execute=runner).compile(checkpointer=saver)
        saved = graph.get_state(config)
        if saved.values and saved.values.get("outcome"):
            result = saved.values
        else:
            result = graph.invoke(None if saved.values else initial, config)
    return {"objective_id": action_id, "revision": context["revision"],
            "thread_id": thread_id, "outcome": result["outcome"],
            "engineering": result.get("engineering"),
            "referee_disposition": result.get("referee_disposition"),
            "attempts": result.get("attempts"),
            "execution_receipt": result.get("execution_receipt"),
            "evidence_manifest_sha256": context["evidence"]["manifest_sha256"],
            "execution_authorized": False,
            "governed_execution_boundary_created": bool(result.get("execution_receipt")),
            "governed_git_promotion_proven": False}


@app.post("/v1/proposals", dependencies=[Depends(require_token)])
async def upload_proposal(request: Request) -> dict[str, str]:
    """Store a bounded, immutable proposal pending deterministic SAGE validation.

    Args:
        request: Authenticated binary ZIP body; never an LLM-generated assertion.
    """
    data = await request.body()
    if not data or len(data) > 6 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="proposal exceeds 6MiB")
    import io

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            files = archive.infolist()
            if (len(files) > 200 or "sage-proposal.json" not in archive.namelist()
                    or sum(item.file_size for item in files) > 48 * 1024 * 1024):
                raise ValueError("invalid or unbounded proposal archive")
            if any(item.filename.startswith("/") or ".." in item.filename.split("/")
                   for item in files):
                raise ValueError("unsafe proposal archive path")
    except (zipfile.BadZipFile, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    root = Path(os.environ.get("SAGE_EXECUTION_PROPOSALS", ""))
    if not str(root) or str(root) == ".":
        raise HTTPException(status_code=503, detail="proposal storage unconfigured")
    digest = hashlib.sha256(data).hexdigest()
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{digest}.zip"
    if path.exists() and path.read_bytes() != data:
        raise HTTPException(status_code=409, detail="content-addressed conflict")
    if not path.exists():
        with tempfile.NamedTemporaryFile(dir=root, delete=False) as tmp:
            pending = Path(tmp.name)
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        try:
            pending.chmod(0o600)
            os.link(pending, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise HTTPException(status_code=409, detail="proposal conflict")
        finally:
            pending.unlink(missing_ok=True)
    return {"package_id": digest, "status": "stored-unverified"}


@app.post("/v1/architecture/ask", dependencies=[Depends(require_token)])
def architecture_ask(request: AdvisoryRequest) -> dict[str, Any]:
    """Provide a Git-grounded Architecture Helper answer across workstations.

    Args:
        request: Question and optional historical Git commit.
    """
    from langgraph.checkpoint.sqlite import SqliteSaver

    with tempfile.TemporaryDirectory(prefix="sage-architecture-") as temp:
        repo = Path(temp) / "repo"
        head = clone_repository(os.environ["SAGE_REPO_URL"], repo)
        revision = pin_revision(repo, request.revision) if request.revision else head
        evidence = compile_evidence(
            repo, revision, request.question,
            os.environ["SAGE_OLLAMA_URL"], os.environ["SAGE_OLLAMA_EMBED_MODEL"],
        )
    digest = stable_digest({"question": request.question, "revision": revision,
                            "evidence_sha256": evidence["manifest_sha256"]})
    config = {"configurable": {"thread_id": "architect-" + digest}}
    call = make_ollama_adapter(
        os.environ["SAGE_OLLAMA_URL"], os.environ["SAGE_OLLAMA_MODEL"],
    )
    with _lock, SqliteSaver.from_conn_string(os.environ["SAGE_CHECKPOINT_DB"]) as saver:
        graph = build_architect_graph(call).compile(checkpointer=saver)
        saved = graph.get_state(config)
        output = (saved.values if saved.values.get("answer")
                  else graph.invoke({"question": request.question, "revision": revision,
                                     "evidence": evidence}, config))
    return {"answer": output["answer"], "revision": revision,
            "evidence_manifest_sha256": evidence["manifest_sha256"],
            "thread_id": config["configurable"]["thread_id"],
            "authority": "read-only architectural proposal; not governed acceptance"}
