"""Safe Makefile aggregate-target composition."""

from __future__ import annotations

from dataclasses import dataclass

from .model import WorkflowError


@dataclass
class MakefileDocument:
    """Parse and mutate Make target prerequisites without recipe injection."""

    lines: list[str]

    @classmethod
    def parse(cls, text: str) -> "MakefileDocument":
        document = cls(text.splitlines())
        document._validate_structure()
        return document

    def _target_range(self, target: str) -> tuple[int, int]:
        matches = [
            index
            for index, line in enumerate(self.lines)
            if line.startswith(f"{target}:")
        ]
        if len(matches) != 1:
            raise WorkflowError(
                f"Expected one Make target {target}, found {len(matches)}"
            )

        start = matches[0]
        end = start
        while self.lines[end].rstrip().endswith("\\"):
            end += 1
            if end >= len(self.lines):
                raise WorkflowError(
                    f"Unterminated Make target continuation: {target}"
                )
            if self.lines[end].startswith("\t"):
                raise WorkflowError(
                    f"Recipe appears inside prerequisite continuation: {target}"
                )
        return start, end

    def _validate_structure(self) -> None:
        for index, line in enumerate(self.lines):
            if line.startswith("\t"):
                continue
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line.startswith(" "):
                previous = self.lines[index - 1] if index else ""
                if not previous.rstrip().endswith("\\"):
                    raise WorkflowError(
                        f"Unexpected indented Makefile line {index + 1}"
                    )

    def dependencies(self, target: str) -> tuple[str, ...]:
        start, end = self._target_range(target)
        fragments = [
            self.lines[start].split(":", 1)[1],
            *self.lines[start + 1 : end + 1],
        ]
        result: list[str] = []
        for fragment in fragments:
            normalized = fragment.strip()
            if normalized.endswith("\\"):
                normalized = normalized[:-1].rstrip()
            result.extend(normalized.split())
        return tuple(result)

    def add_dependency(self, target: str, dependency: str) -> None:
        if not dependency or any(character.isspace() for character in dependency):
            raise WorkflowError(
                f"Invalid Make prerequisite: {dependency!r}"
            )
        if dependency in self.dependencies(target):
            return

        _, end = self._target_range(target)
        self.lines[end] = self.lines[end].rstrip() + " " + dependency
        if dependency not in self.dependencies(target):
            raise WorkflowError(
                f"Failed to add {dependency} to {target}"
            )

    def append_block(self, block: str) -> None:
        normalized = block.strip("\n")
        if not normalized:
            raise WorkflowError("Makefile block must not be empty")
        rendered = self.render()
        if normalized in rendered:
            raise WorkflowError("Makefile block already exists")
        self.lines.extend(["", *normalized.splitlines()])

    def render(self) -> str:
        self._validate_structure()
        return "\n".join(self.lines).rstrip() + "\n"
