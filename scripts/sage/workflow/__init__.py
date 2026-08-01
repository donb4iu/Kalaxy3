"""Reusable, evidence-aware workflow primitives for Kalaxy3 SAGE."""

from .catalog import PrimitiveCatalog
from .composition import Step, Workflow
from .discovery import PreflightResult, SageDiscovery
from .evidence import CloseoutWriter
from .git import GitRepository
from .lifecycle import ImprovementActionClient
from .logging import JsonlEventLogger
from .makefile import MakefileDocument
from .model import (
    CommandResult,
    CommandSpec,
    WorkflowCommandError,
    WorkflowError,
)
from .runner import CommandRunner
from .usage import UsageAnalyzer
from .validation import ValidationCommand, ValidationPlan

FRAMEWORK_VERSION = "0.2.0"

__all__ = [
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
