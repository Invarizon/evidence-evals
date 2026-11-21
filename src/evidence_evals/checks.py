"""Deterministic checks on a system output.

Every check is a pure function: the same output always gives the same verdict. That is the
point. A probabilistic system is judged by repeatable rules fixed in advance, not by whether
the answer sounds convincing.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from .dataset import Case


@dataclass(frozen=True)
class CheckResult:
    type: str
    passed: bool
    detail: str


Check = Callable[[str, Case, dict[str, Any]], tuple[bool, str]]


def _fold(text: str, params: dict[str, Any]) -> str:
    return text if params.get("case_sensitive", False) else text.lower()


def contains_all(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    haystack = _fold(output, params)
    missing = [t for t in params["terms"] if _fold(t, params) not in haystack]
    return (not missing, "all terms present" if not missing else f"missing: {missing}")


def contains_any(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    haystack = _fold(output, params)
    hit = [t for t in params["terms"] if _fold(t, params) in haystack]
    return (bool(hit), f"found: {hit}" if hit else f"none of {params['terms']} found")


def contains_none(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    haystack = _fold(output, params)
    found = [t for t in params["terms"] if _fold(t, params) in haystack]
    return (not found, "no forbidden terms" if not found else f"forbidden terms present: {found}")


def exact(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    ok = output.strip() == str(params["value"]).strip()
    return (ok, "exact match" if ok else "output differs from expected value")


def regex(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    flags = 0 if params.get("case_sensitive", False) else re.IGNORECASE
    ok = re.search(params["pattern"], output, flags) is not None
    return (ok, "pattern found" if ok else f"pattern not found: {params['pattern']}")


def length_between(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    words = len(output.split())
    low, high = params.get("min_words", 0), params.get("max_words", 10**9)
    return (low <= words <= high, f"{words} words (allowed {low} to {high})")


_CITATION = re.compile(r"\[(?:source[: ]*)?([A-Za-z0-9_.-]+)\]")


def cites_source(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    cited = _CITATION.findall(output)
    minimum = params.get("min", 1)
    return (len(cited) >= minimum, f"{len(cited)} citation(s), at least {minimum} required")


def citations_valid(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    cited = set(_CITATION.findall(output))
    unknown = sorted(cited - set(case.sources))
    return (not unknown, "all cited sources exist" if not unknown else f"unknown sources cited: {unknown}")


def grounded_numbers(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    """Every number in the answer must occur in one of the provided sources."""
    corpus = " ".join(case.sources.values())
    allowed = set(re.findall(r"\d+(?:[.,]\d+)?", corpus))
    answer = _CITATION.sub("", output)  # numbers inside citation markers are not claims
    invented = sorted({n for n in re.findall(r"\d+(?:[.,]\d+)?", answer) if n not in allowed})
    return (not invented, "all numbers occur in the sources" if not invented else f"numbers not in sources: {invented}")


def json_valid(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    try:
        data = json.loads(output)
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error.msg}"
    missing = [k for k in params.get("required_keys", []) if not isinstance(data, dict) or k not in data]
    return (not missing, "valid JSON" if not missing else f"missing keys: {missing}")


def refuses(output: str, case: Case, params: dict[str, Any]) -> tuple[bool, str]:
    markers = params.get("markers", ["cannot", "can't", "unable", "kan niet", "niet mogelijk", "weiger"])
    hit = [m for m in markers if m.lower() in output.lower()]
    return (bool(hit), f"refusal marker found: {hit}" if hit else "no refusal marker found")


CHECKS: dict[str, Check] = {
    "contains_all": contains_all,
    "contains_any": contains_any,
    "contains_none": contains_none,
    "exact": exact,
    "regex": regex,
    "length_between": length_between,
    "cites_source": cites_source,
    "citations_valid": citations_valid,
    "grounded_numbers": grounded_numbers,
    "json_valid": json_valid,
    "refuses": refuses,
}


def run_checks(output: str, case: Case) -> list[CheckResult]:
    results: list[CheckResult] = []
    for spec in case.checks:
        name = spec["type"]
        if name not in CHECKS:
            raise ValueError(f"case '{case.id}': unknown check '{name}'. Available: {sorted(CHECKS)}")
        params = {k: v for k, v in spec.items() if k != "type"}
        passed, detail = CHECKS[name](output, case, params)
        results.append(CheckResult(name, passed, detail))
    return results
