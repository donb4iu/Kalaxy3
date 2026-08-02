"""Least-authority read-only Git inspection for Kalaxy3 SAGE."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import CommandResult, CommandSpec, WorkflowError
from .runner import CommandRunner

_SAFE_REF = re.compile(r"^(?:HEAD|@\{upstream\}|[A-Za-z0-9][A-Za-z0-9._/-]*)$")
_FIXED_READ_ONLY = {
    ("branch", "--show-current"),
    ("status", "--porcelain=v1", "--untracked-files=all"),
    ("diff", "--name-only"),
    ("diff", "--cached", "--name-only"),
    ("diff", "--check"),
    ("diff", "--cached", "--check"),
    ("ls-files", "--others", "--exclude-standard"),
}


@dataclass(frozen=True)
class GitAuthoritySnapshot:
    """Read-only repository authority captured from local Git state."""

    path: str
    branch: str
    head: str
    upstream_head: str | None
    working_tree_status: str
    changed_paths: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "branch": self.branch,
            "head": self.head,
            "upstream_head": self.upstream_head,
            "working_tree_status": self.working_tree_status,
            "changed_paths": list(self.changed_paths),
        }


class GitInspector:
    """Expose only an explicit read-only subset of Git commands."""

    def __init__(
        self,
        root: Path,
        runner: CommandRunner,
    ) -> None:
        self.root = root.expanduser().resolve()
        self.runner = runner
        if not (self.root / ".git").exists():
            raise WorkflowError(f"Git repository not found: {self.root}")

    @staticmethod
    def _validate(arguments: tuple[str, ...]) -> None:
        if arguments in _FIXED_READ_ONLY:
            return
        if (
            len(arguments) == 2
            and arguments[0] == "rev-parse"
            and _SAFE_REF.fullmatch(arguments[1])
            and not arguments[1].startswith("-")
            and ".." not in arguments[1]
        ):
            return
        raise WorkflowError(
            "git.inspect rejected non-read-only or unapproved Git arguments: "
            + repr(arguments)
        )

    def run_read_only(
        self,
        arguments: Iterable[str],
        *,
        label: str = "Inspect Git repository state",
        expected_codes: tuple[int, ...] = (0,),
    ) -> CommandResult:
        argv = tuple(arguments)
        self._validate(argv)
        return self.runner.run(
            CommandSpec(
                primitive_id="git.inspect",
                label=label,
                argv=("git", *argv),
                cwd=self.root,
                expected_codes=expected_codes,
            )
        )

    def branch(self) -> str:
        return self.run_read_only(
            ("branch", "--show-current"),
            label="Read active branch",
        ).stdout.rstrip("\n")

    def head(self, reference: str = "HEAD") -> str:
        return self.run_read_only(
            ("rev-parse", reference),
            label=f"Resolve {reference}",
        ).stdout.rstrip("\n")

    def upstream_head(self) -> str | None:
        result = self.run_read_only(
            ("rev-parse", "@{upstream}"),
            label="Resolve local upstream reference",
            expected_codes=(0, 128),
        )
        if result.returncode == 128:
            return None
        return result.stdout.rstrip("\n")

    def status_porcelain(self) -> str:
        return self.run_read_only(
            ("status", "--porcelain=v1", "--untracked-files=all"),
            label="Inspect working-tree state",
        ).stdout.rstrip("\n")

    def changed_paths(self) -> set[str]:
        paths: set[str] = set()
        commands = (
            ("diff", "--name-only"),
            ("diff", "--cached", "--name-only"),
            ("ls-files", "--others", "--exclude-standard"),
        )
        for arguments in commands:
            result = self.run_read_only(
                arguments,
                label="Inspect repository changes",
            )
            paths.update(
                line
                for line in result.stdout.splitlines()
                if line
            )
        return paths

    def staged_paths(self) -> set[str]:
        result = self.run_read_only(
            ("diff", "--cached", "--name-only"),
            label="Inspect staged paths",
        )
        return {
            line
            for line in result.stdout.splitlines()
            if line
        }

    def require_clean(self) -> None:
        observed = self.changed_paths()
        if observed:
            raise WorkflowError(
                f"Working tree must be clean: {sorted(observed)}"
            )

    def require_branch(self, expected: str) -> None:
        actual = self.branch()
        if actual != expected:
            raise WorkflowError(
                f"Expected branch {expected}, found {actual}"
            )

    def require_head(self, expected: str) -> None:
        actual = self.head()
        if actual != expected:
            raise WorkflowError(
                f"Expected HEAD {expected}, found {actual}"
            )

    def require_upstream_equal(self) -> str:
        local = self.head()
        upstream = self.upstream_head()
        if upstream is None:
            raise WorkflowError("Local branch has no upstream reference")
        if local != upstream:
            raise WorkflowError(
                f"Local upstream mismatch: local={local}, upstream={upstream}"
            )
        return local

    def require_exact_paths(
        self,
        expected: Iterable[str],
    ) -> set[str]:
        wanted = set(expected)
        observed = self.changed_paths()
        if observed != wanted:
            raise WorkflowError(
                "Changed-path scope mismatch: "
                f"expected={sorted(wanted)}, observed={sorted(observed)}"
            )
        return observed

    def snapshot(self) -> GitAuthoritySnapshot:
        changed = self.changed_paths()
        staged = self.staged_paths()
        if not changed:
            state = "clean"
        elif staged and staged == changed:
            state = "staged-declared-changes"
        else:
            state = "declared-changes"
        return GitAuthoritySnapshot(
            path=str(self.root),
            branch=self.branch(),
            head=self.head(),
            upstream_head=self.upstream_head(),
            working_tree_status=state,
            changed_paths=tuple(sorted(changed)),
        )
