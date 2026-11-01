"""Narrow SAGE Project status changes; never alter objective or approval records."""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

from .github_inspect import post_project_status_update_graphql
from .projects_inspect import ProjectsInspectionError, inspect_issue_work_item, inspect_project

_ALLOWED_STATUS = frozenset({"Todo", "In Progress", "Blocked"})


class ProjectsOperationError(RuntimeError):
    """Describe a bounded operational update failure without secret exposure."""


def _status_field(project: Mapping[str, Any], desired: str) -> tuple[str, str]:
    """Resolve an existing status option, never create approval fields.

    Args:
        project: Verified Project details.
        desired: Operational status name.
    """
    if desired not in _ALLOWED_STATUS:
        raise ProjectsOperationError("Status is not on the operational allowlist")
    fields = project["fields"]["nodes"]
    matching = [field for field in fields if isinstance(field, dict)
                and field.get("name") == "Status"]
    if (len(matching) != 1 or not isinstance(matching[0].get("id"), str)
            or not isinstance(matching[0].get("options"), list)):
        raise ProjectsOperationError("Project Status field is missing or ambiguous")
    options = [item for item in matching[0]["options"]
               if isinstance(item, dict) and item.get("name") == desired]
    if len(options) != 1 or not isinstance(options[0].get("id"), str):
        raise ProjectsOperationError("Requested status option is absent or ambiguous")
    return str(matching[0]["id"]), options[0]["id"]


def update_operational_status(
    token: str, *, owner: str, project_number: int, repository: str,
    issue_number: int, new_status: str, expected_issue_digest: str,
    expected_status_timestamp: str, actor: str, apply: bool = False,
) -> dict[str, Any]:
    """Validate the exact issue and optionally move only its operational Status.

    Args:
        token: Trusted runtime credential, never supplied to an LLM.
        owner: GitHub Project owner.
        project_number: Project number.
        repository: Canonical owner/repository.
        issue_number: Existing issue identity.
        new_status: Allowlisted operational status, never an approval.
        expected_issue_digest: SHA-256 of Architect work contract previously read.
        expected_status_timestamp: Last observed status change timestamp.
        actor: Trusted executor identity for attribution.
        apply: False produces a proposal; True authorizes bounded mutation.
    """
    if not actor or len(actor) > 128 or not actor.replace("-", "").replace("_", "").isalnum():
        raise ProjectsOperationError("Unattributable executor identity")
    try:
        item = inspect_issue_work_item(token, owner, project_number, repository, issue_number)
        project = inspect_project(token, owner, project_number)["project"]
    except ProjectsInspectionError as exc:
        raise ProjectsOperationError(str(exc)) from None
    digest = hashlib.sha256(item["body"].encode("utf-8")).hexdigest()
    if digest != expected_issue_digest or item["status_updated_at"] != expected_status_timestamp:
        raise ProjectsOperationError("Stale work contract or status; refresh before proposing")
    field_id, option_id = _status_field(project, new_status)
    receipt = {"repository": repository, "issue_number": issue_number,
               "project_number": project_number, "item_id": item["item_id"],
               "previous_status": item["status"], "new_status": new_status,
               "issue_digest": digest, "actor": actor, "applied": False,
               "architect_approval": "not_implied", "concurrency": "best_effort_preflight"}
    if apply and item["status"] != new_status:
        try:
            post_project_status_update_graphql(
                token, project["id"], item["item_id"], field_id, option_id
            )
        except Exception:
            raise ProjectsOperationError("Project status update failed") from None
        receipt["applied"] = True
    return receipt
