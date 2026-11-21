"""Deterministic evidence for probabilistic systems."""

from .checks import CHECKS, CheckResult, run_checks
from .dataset import Case, load_cases
from .report import Report, compare_to_baseline, to_markdown
from .runner import CaseResult, evaluate

__all__ = [
    "CHECKS",
    "Case",
    "CaseResult",
    "CheckResult",
    "Report",
    "compare_to_baseline",
    "evaluate",
    "load_cases",
    "run_checks",
    "to_markdown",
]
__version__ = "0.1.0"
