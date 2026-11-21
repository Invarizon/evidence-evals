"""Evaluation cases: one JSON object per line (JSONL).

A case fixes, in advance, what a good answer looks like. Each entry in ``checks`` is
``{"type": "<check name>", ...parameters}``; see ``checks.py`` for the available checks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Case:
    id: str
    input: str
    checks: list[dict[str, Any]]
    sources: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


def load_cases(path: str | Path) -> list[Case]:
    cases: list[Case] = []
    seen: set[str] = set()
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{number}: invalid JSON ({error.msg})") from error
        for required in ("id", "input", "checks"):
            if required not in raw:
                raise ValueError(f"{path}:{number}: missing field '{required}'")
        if raw["id"] in seen:
            raise ValueError(f"{path}:{number}: duplicate case id '{raw['id']}'")
        seen.add(raw["id"])
        if not raw["checks"]:
            raise ValueError(f"{path}:{number}: case '{raw['id']}' has no checks")
        cases.append(
            Case(
                id=raw["id"],
                input=raw["input"],
                checks=list(raw["checks"]),
                sources=dict(raw.get("sources", {})),
                tags=list(raw.get("tags", [])),
            )
        )
    return cases
