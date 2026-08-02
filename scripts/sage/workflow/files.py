"""Mode-preserving atomic repository file replacement primitives."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import WorkflowError


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    existed: bool
    payload: bytes | None
    mode: int | None


class AtomicFileWriter:
    """Atomically replace declared files while preserving existing modes."""

    def __init__(self, allowed_roots: Iterable[Path]) -> None:
        roots = tuple(
            root.expanduser().resolve()
            for root in allowed_roots
        )
        if not roots:
            raise WorkflowError("At least one allowed root is required")
        self.allowed_roots = roots

    def _resolve(self, path: Path) -> Path:
        candidate = path.expanduser()
        if candidate.exists() and candidate.is_symlink():
            raise WorkflowError(f"Refusing to replace symlink: {candidate}")
        parent = candidate.parent.resolve()
        resolved = parent / candidate.name
        if not any(
            resolved == root or root in resolved.parents
            for root in self.allowed_roots
        ):
            raise WorkflowError(
                f"File path is outside allowed roots: {resolved}"
            )
        return resolved

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def snapshot(self, paths: Iterable[Path]) -> tuple[FileSnapshot, ...]:
        result: list[FileSnapshot] = []
        for path in paths:
            resolved = self._resolve(path)
            if resolved.exists():
                metadata = os.stat(resolved, follow_symlinks=False)
                result.append(
                    FileSnapshot(
                        path=resolved,
                        existed=True,
                        payload=resolved.read_bytes(),
                        mode=stat.S_IMODE(metadata.st_mode),
                    )
                )
            else:
                result.append(
                    FileSnapshot(
                        path=resolved,
                        existed=False,
                        payload=None,
                        mode=None,
                    )
                )
        return tuple(result)

    def write_bytes(
        self,
        path: Path,
        payload: bytes,
        *,
        new_mode: int = 0o644,
    ) -> str:
        resolved = self._resolve(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        if resolved.exists():
            mode = stat.S_IMODE(
                os.stat(resolved, follow_symlinks=False).st_mode
            )
        else:
            mode = new_mode

        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{resolved.name}.",
            dir=resolved.parent,
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, mode)
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, resolved)
            self._fsync_directory(resolved.parent)
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            temporary.unlink(missing_ok=True)
            raise
        return hashlib.sha256(payload).hexdigest()

    def write_text(
        self,
        path: Path,
        text: str,
        *,
        new_mode: int = 0o644,
    ) -> str:
        return self.write_bytes(
            path,
            text.encode("utf-8"),
            new_mode=new_mode,
        )

    def restore(self, snapshots: Iterable[FileSnapshot]) -> None:
        for item in reversed(tuple(snapshots)):
            if item.existed:
                if item.payload is None or item.mode is None:
                    raise WorkflowError(
                        f"Incomplete snapshot for {item.path}"
                    )
                self.write_bytes(
                    item.path,
                    item.payload,
                    new_mode=item.mode,
                )
                os.chmod(item.path, item.mode, follow_symlinks=False)
            else:
                resolved = self._resolve(item.path)
                resolved.unlink(missing_ok=True)
                self._fsync_directory(resolved.parent)


class AtomicFileTransaction:
    """Rollback a declared file set unless the transaction is committed."""

    def __init__(
        self,
        writer: AtomicFileWriter,
        paths: Iterable[Path],
    ) -> None:
        self.writer = writer
        self.snapshots = writer.snapshot(paths)
        self._committed = False

    def write_bytes(
        self,
        path: Path,
        payload: bytes,
        *,
        new_mode: int = 0o644,
    ) -> str:
        return self.writer.write_bytes(path, payload, new_mode=new_mode)

    def write_text(
        self,
        path: Path,
        text: str,
        *,
        new_mode: int = 0o644,
    ) -> str:
        return self.writer.write_text(path, text, new_mode=new_mode)

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        self.writer.restore(self.snapshots)
        self._committed = True

    def __enter__(self) -> "AtomicFileTransaction":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if not self._committed:
            self.writer.restore(self.snapshots)
        return False
