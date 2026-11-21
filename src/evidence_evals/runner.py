"""Run a system over cases, repeat to expose non-determinism, and collect evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .checks import CheckResult, run_checks
from .dataset import Case
from .report import Report


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    tags: list[str]
    runs: int
    passes: int
    failures: list[str]  # details of failed checks across runs (deduplicated)

    @property
    def pass_rate(self) -> float:
        return self.passes / self.runs

    @property
    def stable(self) -> bool:
        """True when every run gave the same verdict."""
        return self.passes in (0, self.runs)

    @property
    def passed(self) -> bool:
        return self.passes == self.runs


def evaluate(system: Callable[[str], str], cases: list[Case], repeats: int = 1) -> Report:
    """Run ``system`` on every case ``repeats`` times. A case passes only if all runs pass."""
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    results: list[CaseResult] = []
    for case in cases:
        passes = 0
        failures: list[str] = []
        for _ in range(repeats):
            output = system(case.input)
            checks: list[CheckResult] = run_checks(output, case)
            if all(c.passed for c in checks):
                passes += 1
            else:
                for c in checks:
                    if not c.passed and f"{c.type}: {c.detail}" not in failures:
                        failures.append(f"{c.type}: {c.detail}")
        results.append(CaseResult(case.id, list(case.tags), repeats, passes, failures))
    return Report(results=results, repeats=repeats)
