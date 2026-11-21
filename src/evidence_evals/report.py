"""Reports and regression comparison."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .runner import CaseResult


@dataclass
class Report:
    results: list["CaseResult"]
    repeats: int

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    @property
    def unstable(self) -> list[str]:
        return [r.case_id for r in self.results if not r.stable]

    def to_dict(self) -> dict:
        return {
            "repeats": self.repeats,
            "total": self.total,
            "passed": self.passed,
            "pass_rate": round(self.pass_rate, 4),
            "unstable": self.unstable,
            "cases": {r.case_id: {"passed": r.passed, "pass_rate": round(r.pass_rate, 4), "failures": r.failures} for r in self.results},
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def compare_to_baseline(report: Report, baseline: dict) -> dict[str, list[str]]:
    """Compare with an earlier report (``Report.to_dict()``).

    ``regressions``: passed before, fails now. ``fixed``: failed before, passes now.
    ``new``/``removed``: cases that appear in only one of the two runs.
    """
    before = baseline.get("cases", {})
    now = {r.case_id: r.passed for r in report.results}
    return {
        "regressions": sorted(c for c, ok in now.items() if c in before and before[c]["passed"] and not ok),
        "fixed": sorted(c for c, ok in now.items() if c in before and not before[c]["passed"] and ok),
        "new": sorted(c for c in now if c not in before),
        "removed": sorted(c for c in before if c not in now),
    }


def to_markdown(report: Report, comparison: dict[str, list[str]] | None = None) -> str:
    lines = [
        "# Evaluation report",
        "",
        f"- Cases: {report.total}",
        f"- Passed: {report.passed} ({report.pass_rate:.0%})",
        f"- Runs per case: {report.repeats}",
    ]
    if report.unstable:
        lines.append(f"- Unstable cases (different verdicts across runs): {', '.join(report.unstable)}")
    if comparison:
        lines += ["", "## Compared with baseline", ""]
        for key in ("regressions", "fixed", "new", "removed"):
            lines.append(f"- {key}: {', '.join(comparison[key]) or 'none'}")
    failed = [r for r in report.results if not r.passed]
    if failed:
        lines += ["", "## Failed cases", ""]
        for r in failed:
            lines.append(f"- **{r.case_id}** ({r.passes}/{r.runs} runs passed)")
            lines += [f"  - {f}" for f in r.failures]
    return "\n".join(lines) + "\n"
