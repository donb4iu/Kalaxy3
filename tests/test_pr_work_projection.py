"""Regression tests for SAGE's plain-language PR work projection."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/sage/architecture_helper/pr_work_projection.py"
SPEC = importlib.util.spec_from_file_location("pr_work_projection", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sample() -> dict[str, Any]:
    """Load the grounded PR #62 example as an untrusted input fixture."""
    return json.loads((ROOT / "examples/pr62-work-thread.json").read_text())


class ProjectionTests(unittest.TestCase):
    """Require honest, readable output without implicit approval."""

    def test_projected_example(self) -> None:
        """Render the actual PR #62 scenario without asserting verification."""
        data = MODULE.project(MODULE.validate_thread(sample()))
        self.assertEqual(data["schema"], "sage-architecture-work-projection-v1")
        self.assertIn("not_qualified", data["gate"])
        self.assertEqual(data["inquiries"], [])

    def test_missing_inquiry_visible(self) -> None:
        """A missing retrieval record cannot become a no-prior-art claim."""
        page = MODULE.html_page(MODULE.project(MODULE.validate_thread(sample())))
        self.assertIn("No inquiry record supplied", page)
        self.assertIn("not evidence that no prior art exists", page)

    def test_html_escapes_untrusted_work(self) -> None:
        """Prevent candidate metadata from injecting scripts into a dashboard."""
        item = sample()
        item["objective"]["title"] = "<script>alert(1)</script>"
        page = MODULE.html_page(MODULE.project(MODULE.validate_thread(item)))
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_no_fabricated_signature_validation(self) -> None:
        """Even a supplied digest remains unqualified by this projection."""
        item = sample()
        item["inquiries"] = [{"question": "What exists?", "results": [],
                              "gaps": ["Could not locate build path"],
                              "receipt_sha256": "f" * 64}]
        record = MODULE.project(MODULE.validate_thread(item))
        self.assertEqual(record["inquiries"][0]["record_authenticity"],
                         "not_verified_by_projection")

    def test_architect_iteration_preserved(self) -> None:
        """Preserve Architect feedback and revised proposal in order."""
        record = MODULE.project(MODULE.validate_thread(sample()))
        self.assertEqual(len(record["iterations"]), 2)
        self.assertIn("GitHub Actions", record["iterations"][0]["question"])

    def test_concept_relationships_visible(self) -> None:
        """Show known implementation reuse and knowledge gaps side by side."""
        page = MODULE.html_page(MODULE.project(MODULE.validate_thread(sample())))
        self.assertIn("Where does this fit?", page)
        self.assertIn("Multi-architecture container publication", page)

    def test_invalid_schema_fails(self) -> None:
        """Reject records claiming an unsupported schema."""
        item = sample()
        item["schema"] = "different"
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.validate_thread(item)

    def test_bounded_records(self) -> None:
        """Reject unbounded input rather than render a misleading overview."""
        item = sample()
        item["iterations"] = [{}] * 31
        with self.assertRaises(MODULE.ProjectionError):
            MODULE.validate_thread(item)

    def test_cli_writes_both_projections(self) -> None:
        """Write deterministic JSON and HTML from an existing local fixture."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            document = MODULE.project(MODULE.validate_thread(sample()))
            (output / "projection.json").write_text(json.dumps(document))
            (output / "dashboard.html").write_text(MODULE.html_page(document))
            self.assertIn("What did we look up?",
                          (output / "dashboard.html").read_text())


if __name__ == "__main__":
    unittest.main()
