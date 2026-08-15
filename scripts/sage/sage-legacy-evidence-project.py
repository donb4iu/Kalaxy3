#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))
from legacy_evidence_projection import LegacyEvidenceError, build_projection, write_projection

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--projection-id", required=True)
    p.add_argument("--source-file", type=Path, required=True)
    p.add_argument("--source-descriptor", type=Path, required=True)
    p.add_argument("--claims", type=Path, required=True)
    p.add_argument("--projector-class", choices=("human","llm","deterministic-orchestrator"), required=True)
    p.add_argument("--projector-identity", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        source_bytes = a.source_file.expanduser().resolve().read_bytes()
        descriptor = json.loads(a.source_descriptor.expanduser().resolve().read_text())
        claims = json.loads(a.claims.expanduser().resolve().read_text())
        record = build_projection(
            projection_id=a.projection_id,
            source_descriptor=descriptor,
            source_bytes=source_bytes,
            claims=claims,
            projected_by={"participant_class":a.projector_class,"identity":a.projector_identity},
        )
        digest = write_projection(a.output, record)
    except (OSError, json.JSONDecodeError, LegacyEvidenceError, TypeError, ValueError) as error:
        print("Kalaxy3 SAGE legacy evidence projection: FAIL CLOSED")
        print(f"  - {error}")
        return 2
    print("Kalaxy3 SAGE legacy evidence projection: PASS")
    print(f"Projection: {a.output.expanduser().resolve()}")
    print(f"SHA-256: {digest}")
    print("Current authority granted: no")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
