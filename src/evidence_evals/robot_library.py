"""Robot Framework library: use deterministic evidence checks as keywords.

    *** Settings ***
    Library    evidence_evals.robot_library.EvidenceEvals

Install with ``pip install evidence-evals[robot]``.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from .dataset import load_cases
from .runner import evaluate


class EvidenceEvals:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self) -> None:
        self._report = None

    def run_evaluation(self, dataset: str, system: str, repeats: int = 1) -> float:
        """Run ``system`` ('module:function') on the dataset and return the pass rate (0 to 1)."""
        module_name, _, function_name = system.partition(":")
        sys.path.insert(0, str(Path.cwd()))
        function = getattr(importlib.import_module(module_name), function_name)
        self._report = evaluate(function, load_cases(dataset), repeats=int(repeats))
        return self._report.pass_rate

    def pass_rate_should_be_at_least(self, minimum: float) -> None:
        """Fail unless the last evaluation reached ``minimum`` (0 to 1)."""
        assert self._report is not None, "Run Evaluation first"
        rate = self._report.pass_rate
        if rate < float(minimum):
            failed = [r.case_id for r in self._report.results if not r.passed]
            raise AssertionError(f"Pass rate {rate:.0%} is below {float(minimum):.0%}. Failed: {failed}")

    def no_unstable_cases(self) -> None:
        """Fail if any case gave different verdicts across repeated runs."""
        assert self._report is not None, "Run Evaluation first"
        if self._report.unstable:
            raise AssertionError(f"Unstable cases: {self._report.unstable}")
