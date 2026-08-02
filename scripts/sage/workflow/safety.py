"""Production helper Git, GitHub, credential, and deployment safety guardrail."""

from __future__ import annotations

import ast
import shlex
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_READ_ONLY_GIT = {
    ("git", "branch", "--show-current"),
    ("git", "status", "--porcelain=v1", "--untracked-files=all"),
    ("git", "diff", "--name-only"),
    ("git", "diff", "--cached", "--name-only"),
    ("git", "diff", "--check"),
    ("git", "diff", "--cached", "--check"),
    ("git", "ls-files", "--others", "--exclude-standard"),
    ("git", "rev-parse", "HEAD"),
    ("git", "rev-parse", "@{upstream}"),
}
_MUTATING_GIT = {
    "add",
    "am",
    "apply",
    "branch",
    "checkout",
    "cherry-pick",
    "clean",
    "commit",
    "fetch",
    "merge",
    "mv",
    "pull",
    "push",
    "rebase",
    "reset",
    "restore",
    "revert",
    "rm",
    "switch",
    "tag",
    "update-ref",
}
_CREDENTIAL_NAMES = {
    "GH_CONFIG_DIR",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
}
_GIT_REPOSITORY_MUTATORS = {
    "commit_and_push",
    "create_branch",
    "fetch",
}


@dataclass(frozen=True)
class GitSafetyViolation:
    path: str
    line: int
    code: str
    message: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.code}: {self.message}"


class GitSafetyGuardrail:
    """Statically reject helper paths that can mutate protected systems."""

    @staticmethod
    def _literal_sequence(node: ast.AST | None) -> tuple[str, ...] | None:
        if isinstance(node, (ast.Tuple, ast.List)):
            values: list[str] = []
            for item in node.elts:
                if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                    return None
                values.append(item.value)
            return tuple(values)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                return tuple(shlex.split(node.value))
            except ValueError:
                return None
        return None

    @staticmethod
    def _call_name(node: ast.Call) -> str:
        target = node.func
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute):
            parts = [target.attr]
            current = target.value
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""

    @classmethod
    def _command_from_call(cls, node: ast.Call) -> tuple[str, ...] | None:
        name = cls._call_name(node)
        if name.endswith("CommandSpec"):
            for keyword in node.keywords:
                if keyword.arg == "argv":
                    return cls._literal_sequence(keyword.value)
            return None
        if name in {
            "subprocess.run",
            "subprocess.Popen",
            "subprocess.call",
            "subprocess.check_call",
            "subprocess.check_output",
            "os.system",
        }:
            if not node.args:
                return None
            return cls._literal_sequence(node.args[0])
        return None

    @staticmethod
    def _is_temp_fixture(path: Path, fixture_root: Path | None) -> bool:
        if fixture_root is None:
            return False
        resolved_path = path.expanduser().resolve()
        resolved_root = fixture_root.expanduser().resolve()
        temp_root = Path(tempfile.gettempdir()).resolve()
        return (
            (resolved_path == resolved_root or resolved_root in resolved_path.parents)
            and (resolved_root == temp_root or temp_root in resolved_root.parents)
        )

    @classmethod
    def _command_violations(
        cls,
        path: Path,
        line: int,
        argv: tuple[str, ...],
        *,
        allow_fixture_mutation: bool,
        fixture_root: Path | None,
    ) -> list[GitSafetyViolation]:
        if not argv:
            return []
        fixture_allowed = allow_fixture_mutation and cls._is_temp_fixture(path, fixture_root)
        command = argv[0]
        if command == "git":
            if argv in _READ_ONLY_GIT:
                return []
            subcommand = argv[1] if len(argv) > 1 else ""
            if fixture_allowed and subcommand in _MUTATING_GIT:
                return []
            return [
                GitSafetyViolation(
                    str(path),
                    line,
                    "GIT-MUTATION",
                    f"unapproved Git command {argv!r}",
                )
            ]
        if command == "gh":
            return [
                GitSafetyViolation(
                    str(path),
                    line,
                    "GITHUB-MUTATION",
                    "downloaded helpers may not invoke gh",
                )
            ]
        if command == "kubectl" and len(argv) > 1 and argv[1] in {
            "apply", "create", "delete", "edit", "label", "patch", "replace", "rollout", "scale", "set"
        }:
            return [GitSafetyViolation(str(path), line, "DEPLOYMENT-MUTATION", repr(argv))]
        if command == "helm" and len(argv) > 1 and argv[1] in {
            "install", "rollback", "uninstall", "upgrade"
        }:
            return [GitSafetyViolation(str(path), line, "DEPLOYMENT-MUTATION", repr(argv))]
        if command in {"ansible-playbook", "terraform", "tofu"}:
            return [GitSafetyViolation(str(path), line, "DEPLOYMENT-MUTATION", repr(argv))]
        if command == "make" and len(argv) > 1 and any(
            target == "deploy" or target == "uninstall" or target.startswith("phase-")
            for target in argv[1:]
        ):
            return [GitSafetyViolation(str(path), line, "DEPLOYMENT-MUTATION", repr(argv))]
        return []

    @classmethod
    def scan_source(
        cls,
        source: str,
        *,
        path: Path,
        allow_fixture_mutation: bool = False,
        fixture_root: Path | None = None,
    ) -> tuple[GitSafetyViolation, ...]:
        tree = ast.parse(source, filename=str(path))
        violations: list[GitSafetyViolation] = []
        fixture_allowed = allow_fixture_mutation and cls._is_temp_fixture(path, fixture_root)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "subprocess" and not fixture_allowed:
                        violations.append(
                            GitSafetyViolation(
                                str(path), node.lineno, "DIRECT-SUBPROCESS",
                                "production helpers must use repository command primitives",
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module == "subprocess" and not fixture_allowed:
                    violations.append(
                        GitSafetyViolation(
                            str(path), node.lineno, "DIRECT-SUBPROCESS",
                            "production helpers must use repository command primitives",
                        )
                    )
                for alias in node.names:
                    if alias.name == "GitRepository" and not fixture_allowed:
                        violations.append(
                            GitSafetyViolation(
                                str(path), node.lineno, "MIXED-GIT-AUTHORITY",
                                "GitRepository exposes prohibited mutation methods",
                            )
                        )
            elif isinstance(node, ast.Call):
                name = cls._call_name(node)
                if name.split(".")[-1] in _GIT_REPOSITORY_MUTATORS and not fixture_allowed:
                    violations.append(
                        GitSafetyViolation(
                            str(path), node.lineno, "GIT-MUTATION-API",
                            f"prohibited mutation method {name}",
                        )
                    )
                argv = cls._command_from_call(node)
                if argv is not None:
                    violations.extend(
                        cls._command_violations(
                            path,
                            node.lineno,
                            argv,
                            allow_fixture_mutation=allow_fixture_mutation,
                            fixture_root=fixture_root,
                        )
                    )
                if isinstance(node.func, ast.Attribute) and node.func.attr in {"get", "pop", "setdefault"}:
                    if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value in _CREDENTIAL_NAMES:
                        violations.append(
                            GitSafetyViolation(
                                str(path), node.lineno, "CREDENTIAL-INHERITANCE",
                                f"access to {node.args[0].value} is prohibited in generated helpers",
                            )
                        )
            elif isinstance(node, ast.Subscript):
                value = node.value
                is_environment = (
                    isinstance(value, ast.Attribute)
                    and isinstance(value.value, ast.Name)
                    and value.value.id == "os"
                    and value.attr == "environ"
                )
                if is_environment:
                    key = node.slice
                    if isinstance(key, ast.Constant) and key.value in _CREDENTIAL_NAMES:
                        violations.append(
                            GitSafetyViolation(
                                str(path), node.lineno, "CREDENTIAL-INHERITANCE",
                                f"access to {key.value} is prohibited in generated helpers",
                            )
                        )
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and target.id in _CREDENTIAL_NAMES:
                        violations.append(
                            GitSafetyViolation(
                                str(path), node.lineno, "CREDENTIAL-EMBEDDING",
                                f"generated helper defines {target.id}",
                            )
                        )

        deduplicated = {
            (item.path, item.line, item.code, item.message): item
            for item in violations
        }
        return tuple(
            deduplicated[key]
            for key in sorted(deduplicated)
        )

    @classmethod
    def scan_paths(
        cls,
        paths: Iterable[Path],
        *,
        allow_fixture_mutation: bool = False,
        fixture_root: Path | None = None,
    ) -> tuple[GitSafetyViolation, ...]:
        violations: list[GitSafetyViolation] = []
        for path in paths:
            violations.extend(
                cls.scan_source(
                    path.read_text(encoding="utf-8"),
                    path=path,
                    allow_fixture_mutation=allow_fixture_mutation,
                    fixture_root=fixture_root,
                )
            )
        return tuple(violations)
