#!/usr/bin/env python3
"""Unit tests for the functional translation isolation boundary."""

from __future__ import annotations

import copy
import unittest
from typing import Any

from functional_handoff_boundary import (
    ContractError,
    digest,
    validate_disposition,
    validate_handoff,
)


def handoff_fixture() -> dict[str, Any]:
    """Build a valid objective-centric functional request."""
    return {
        "schema_version": "1.0",
        "objective_id": "SAGE-HUMAN-WORKBENCH",
        "parent_objective_id": None,
        "functional_goal": "Deliver a browser-accessible human workbench",
        "current_maturity": "planning; implementation not verified",
        "verified_progress": [],
        "outstanding_functional_work": "Deliver a minimum usable dashboard",
        "success_evidence": ["Browser review of objective and decision views"],
        "constraints": ["Read-only access", "Preserve uncertainty"],
        "evidence_refs": [],
    }


def disposition_fixture(handoff: dict[str, Any]) -> dict[str, Any]:
    """Build a valid single-decision translator result.

    Args:
        handoff: The request whose hash the response must bind.
    """
    return {
        "schema_version": "1.0",
        "handoff_sha256": digest(handoff),
        "disposition": "executable",
        "functional_contribution": "Initial stakeholder-readable objective view",
        "sage_capabilities": ["governed request planning"],
        "validation": ["Read-only dashboard review"],
        "reason": "An existing path can deliver a UI slice",
        "clarification_question": None,
        "blocker": None,
        "next_functional_step": "Implement browser-visible objective view",
    }


class BoundaryTests(unittest.TestCase):
    """Verify fail-closed validation of function-only handoffs."""

    def test_valid(self) -> None:
        """A bounded functional request and response pass."""
        request = handoff_fixture()
        validate_handoff(request)
        validate_disposition(disposition_fixture(request), request)

    def test_execution_injection(self) -> None:
        """A persistent agent cannot inject an execution primitive."""
        request = handoff_fixture()
        request["git_command"] = "git push --force"
        with self.assertRaises(ContractError):
            validate_handoff(request)

    def test_context_injection(self) -> None:
        """Unfiltered conversation history cannot cross the boundary."""
        request = handoff_fixture()
        request["conversation_history"] = "historical dialogue"
        with self.assertRaises(ContractError):
            validate_handoff(request)

    def test_stale_response(self) -> None:
        """A response for another functional request fails closed."""
        request = handoff_fixture()
        result = disposition_fixture(request)
        changed = copy.deepcopy(request)
        changed["functional_goal"] = "Deliver another objective"
        with self.assertRaises(ContractError):
            validate_disposition(result, changed)

    def test_clarification(self) -> None:
        """Clarification must ask an explicit functional question."""
        request = handoff_fixture()
        result = disposition_fixture(request)
        result["disposition"] = "clarify"
        with self.assertRaises(ContractError):
            validate_disposition(result, request)
        result["clarification_question"] = "Which stakeholders need access?"
        validate_disposition(result, request)

    def test_blocked(self) -> None:
        """A blocking disposition must name its material blocker."""
        request = handoff_fixture()
        result = disposition_fixture(request)
        result["disposition"] = "blocked"
        with self.assertRaises(ContractError):
            validate_disposition(result, request)
        result["blocker"] = "Required SAGE capability not available"
        validate_disposition(result, request)


if __name__ == "__main__":
    unittest.main()
