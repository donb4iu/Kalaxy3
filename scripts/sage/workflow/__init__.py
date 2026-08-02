"""Reusable, evidence-aware workflow primitives for Kalaxy3 SAGE."""

from .catalog import PrimitiveCatalog
from .composition import Step, Workflow
from .discovery import PreflightResult, SageDiscovery
from .evidence import CloseoutWriter
from .files import AtomicFileTransaction, AtomicFileWriter, FileSnapshot
from .git import GitRepository
from .git_inspect import GitAuthoritySnapshot, GitInspector
from .lifecycle import ImprovementActionClient
from .logging import JsonlEventLogger
from .makefile import MakefileDocument
from .proposal import OperatorGitProposal
from .safety import GitSafetyGuardrail, GitSafetyViolation
from .model import (
    CommandResult,
    CommandSpec,
    WorkflowCommandError,
    WorkflowError,
)
from .runner import CommandRunner
from .usage import UsageAnalyzer
from .validation import ValidationCommand, ValidationPlan

FRAMEWORK_VERSION = "0.3.0"

__all__ = [
    "AtomicFileTransaction",
    "AtomicFileWriter",
    "FileSnapshot",
    "GitAuthoritySnapshot",
    "GitInspector",
    "GitSafetyGuardrail",
    "GitSafetyViolation",
    "OperatorGitProposal",
    "CloseoutWriter",
    "CommandResult",
    "CommandRunner",
    "CommandSpec",
    "FRAMEWORK_VERSION",
    "GitRepository",
    "ImprovementActionClient",
    "JsonlEventLogger",
    "MakefileDocument",
    "PreflightResult",
    "PrimitiveCatalog",
    "SageDiscovery",
    "Step",
    "UsageAnalyzer",
    "ValidationCommand",
    "ValidationPlan",
    "Workflow",
    "WorkflowCommandError",
    "WorkflowError",
]
