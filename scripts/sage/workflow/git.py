"""Reusable Git repository-state and exact-scope mutation primitives."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .model import CommandSpec, WorkflowError
from .runner import CommandRunner


class GitRepository:
    """Fail-closed Git operations with exact path and synchronization checks."""

    def __init__(
        self,
        root: Path,
        runner: CommandRunner,
        *,
        remote: str = "origin",
    ) -> None:
        self.root = root.expanduser().resolve()
        self.runner = runner
        self.remote = remote
        if not (self.root / ".git").exists():
            raise WorkflowError(f"Git repository not found: {self.root}")

    def _git(
        self,
        label: str,
        *arguments: str,
        expected_codes: tuple[int, ...] = (0,),
    ) -> str:
        result = self.runner.run(
            CommandSpec(
                primitive_id="git.repository",
                label=label,
                argv=("git", *arguments),
                cwd=self.root,
                expected_codes=expected_codes,
            )
        )
        return result.stdout.strip()

    def fetch(self) -> None:
        self._git(
            "Fetch remote repository state",
            "fetch",
            self.remote,
            "--prune",
        )

    def branch(self) -> str:
        return self._git(
            "Read active branch",
            "branch",
            "--show-current",
        )

    def head(self, reference: str = "HEAD") -> str:
        return self._git(
            f"Resolve {reference}",
            "rev-parse",
            reference,
        )

    def changed_paths(self) -> set[str]:
        paths: set[str] = set()
        commands = (
            ("diff", "--name-only"),
            ("diff", "--cached", "--name-only"),
            ("ls-files", "--others", "--exclude-standard"),
        )
        for arguments in commands:
            paths.update(
                item
                for item in self._git(
                    "Inspect repository changes",
                    *arguments,
                ).splitlines()
                if item
            )
        return paths

    def staged_paths(self) -> set[str]:
        return {
            item
            for item in self._git(
                "Inspect staged paths",
                "diff",
                "--cached",
                "--name-only",
            ).splitlines()
            if item
        }

    def require_clean(self) -> None:
        paths = self.changed_paths()
        if paths:
            raise WorkflowError(
                f"Working tree must be clean: {sorted(paths)}"
            )

    def require_branch(self, expected: str) -> None:
        actual = self.branch()
        if actual != expected:
            raise WorkflowError(
                f"Expected branch {expected}, found {actual}"
            )

    def require_synced(self, branch: str) -> str:
        self.fetch()
        local = self.head("HEAD")
        remote = self.head(f"{self.remote}/{branch}")
        if local != remote:
            raise WorkflowError(
                f"Branch is not synchronized: "
                f"local={local}, remote={remote}"
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
                f"Changed-path scope mismatch: "
                f"expected={sorted(wanted)}, "
                f"observed={sorted(observed)}"
            )
        return observed

    def create_branch(
        self,
        branch: str,
        *,
        apply: bool,
    ) -> None:
        if not apply:
            raise WorkflowError(
                "Branch creation requires explicit apply=True"
            )
        self.require_clean()
        self._git(
            f"Create feature branch {branch}",
            "switch",
            "-c",
            branch,
        )
        self._git(
            f"Push feature branch {branch}",
            "push",
            "-u",
            self.remote,
            branch,
        )
        self.require_synced(branch)

    def commit_and_push(
        self,
        *,
        branch: str,
        exact_paths: Iterable[str],
        message: str,
        apply: bool,
    ) -> str:
        """Commit exactly declared paths and push a synchronized branch."""

        if not apply:
            raise WorkflowError(
                "Commit and push requires explicit apply=True"
            )
        paths = sorted(set(exact_paths))
        if not paths:
            raise WorkflowError("exact_paths must not be empty")

        self.require_branch(branch)
        self.require_exact_paths(paths)
        self._git("Check diff whitespace", "diff", "--check")
        self._git(
            "Stage exact mutation scope",
            "add",
            "--",
            *paths,
        )
        staged = self.staged_paths()
        if staged != set(paths):
            raise WorkflowError(
                f"Staged-path scope mismatch: {sorted(staged)}"
            )
        self._git(
            "Check staged diff whitespace",
            "diff",
            "--cached",
            "--check",
        )
        self._git(
            f"Commit {message}",
            "commit",
            "-m",
            message,
        )
        commit = self.head("HEAD")
        self._git(
            f"Push {branch}",
            "push",
            self.remote,
            branch,
        )
        self.require_clean()
        self.require_synced(branch)
        return commit
