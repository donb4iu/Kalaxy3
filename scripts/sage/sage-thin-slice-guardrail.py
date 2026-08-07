#!/usr/bin/env python3
"""Fail closed when the SAGE thin-slice model or generated views drift."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/sage/sage-thin-slice.py"


def load_cli() -> object:
    spec = importlib.util.spec_from_file_location("sage_thin_slice", CLI)
    if spec is None or spec.loader is None:
        raise RuntimeError("thin-slice module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    try:
        module = load_cli()
        value = module.load(ROOT)
        failures = module.validate(value)
        if failures:
            raise RuntimeError("; ".join(failures))
        view = module.render(value).rstrip() + "\n"
        metrics = json.dumps(module.metrics(value), indent=2, ensure_ascii=False).rstrip() + "\n"
        if (ROOT / module.VIEW).read_text(encoding="utf-8") != view:
            raise RuntimeError("rendered thin-slice view differs")
        if (ROOT / module.METRICS).read_text(encoding="utf-8") != metrics:
            raise RuntimeError("thin-slice metrics snapshot differs")
        self_failures = module.self_test(value)
        if self_failures:
            raise RuntimeError("; ".join(self_failures))
    except (OSError, RuntimeError, ValueError) as error:
        print("Kalaxy3 SAGE thin-slice guardrail: FAIL CLOSED")
        print(f"  - {error}")
        return 1
    print("PASS coherent public introduction and selected real case")
    print("PASS source, SAGE, and human authority separation")
    print("PASS end-to-end trace, evidence, measures, and unknowns")
    print("PASS wider participation and reusable future capability")
    print("Kalaxy3 SAGE thin-slice guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
