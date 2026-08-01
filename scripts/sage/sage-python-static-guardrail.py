#!/usr/bin/env python3
"""Source-only undefined-global guardrail for Kalaxy3 Python workflows."""

from __future__ import annotations

import argparse
import builtins
import symtable
import tempfile
from pathlib import Path
from typing import Iterable

_IMPLICIT_GLOBALS = {
    "__builtins__",
    "__cached__",
    "__file__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
}


def module_definitions(table: symtable.SymbolTable) -> set[str]:
    """Return names bound by a module symbol table."""

    definitions = set(_IMPLICIT_GLOBALS)
    definitions.update(dir(builtins))
    for symbol in table.get_symbols():
        if (
            symbol.is_assigned()
            or symbol.is_imported()
            or symbol.is_namespace()
            or symbol.is_parameter()
        ):
            definitions.add(symbol.get_name())
    return definitions


def undefined_globals(
    source: str,
    *,
    filename: str,
) -> tuple[str, ...]:
    """Return referenced global names not defined by the module or builtins."""

    root = symtable.symtable(source, filename, "exec")
    definitions = module_definitions(root)
    failures: set[str] = set()

    def inspect(table: symtable.SymbolTable) -> None:
        for symbol in table.get_symbols():
            name = symbol.get_name()
            if (
                symbol.is_referenced()
                and symbol.is_global()
                and name not in definitions
            ):
                failures.add(name)
        for child in table.get_children():
            inspect(child)

    inspect(root)
    return tuple(sorted(failures))


def python_paths(values: Iterable[Path]) -> tuple[Path, ...]:
    """Expand explicit files and directories into unique Python paths."""

    result: set[Path] = set()
    for value in values:
        path = value.expanduser()
        if path.is_dir():
            result.update(path.rglob("*.py"))
        elif path.suffix == ".py":
            result.add(path)
        else:
            raise ValueError(
                f"Static-analysis path is not Python: {path}"
            )
    return tuple(sorted(result))


def self_test() -> int:
    positive = """from __future__ import annotations
import json
CONSTANT = "ok"
def render(value: str) -> str:
    return json.dumps({"value": value, "constant": CONSTANT})
"""
    if undefined_globals(positive, filename="positive.py"):
        raise RuntimeError("positive static fixture failed")

    negative = """def register_action():
    return FAILURE_EVIDENCE
"""
    observed = undefined_globals(
        negative,
        filename="negative.py",
    )
    if observed != ("FAILURE_EVIDENCE",):
        raise RuntimeError(
            f"undefined-name fixture mismatch: {observed}"
        )

    closure = """VALUE = "ok"
def outer():
    local = "value"
    def inner():
        return VALUE + local
    return inner()
"""
    if undefined_globals(closure, filename="closure.py"):
        raise RuntimeError("closure static fixture failed")

    with tempfile.TemporaryDirectory(
        prefix="sage-python-static-self-test-"
    ) as raw:
        path = Path(raw) / "negative.py"
        path.write_text(negative, encoding="utf-8")
        if python_paths((path,)) != (path,):
            raise RuntimeError("path expansion fixture failed")

    print("PASS valid module, builtin, and closure references")
    print("PASS undefined global regression fixture")
    print("PASS deterministic Python path expansion")
    print("Kalaxy3 Python static guardrail self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    requested = args.paths or [
        Path("scripts/sage/workflow"),
        Path("scripts/sage/workflows"),
    ]
    failures: list[str] = []
    for path in python_paths(requested):
        source = path.read_text(encoding="utf-8")
        for name in undefined_globals(
            source,
            filename=str(path),
        ):
            failures.append(
                f"{path}: undefined global reference {name}"
            )

    if failures:
        print("Kalaxy3 Python static guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        f"PASS undefined-global analysis for "
        f"{len(python_paths(requested))} Python paths"
    )
    print("Kalaxy3 Python static guardrail: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        SyntaxError,
        TypeError,
        ValueError,
    ) as error:
        print("Kalaxy3 Python static guardrail: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
