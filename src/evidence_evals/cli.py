"""Command line: evidence-evals run --dataset cases.jsonl --system module:function"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from .dataset import load_cases
from .report import compare_to_baseline, to_markdown
from .runner import evaluate


def _load_system(spec: str):
    module_name, _, function_name = spec.partition(":")
    if not function_name:
        raise SystemExit("--system must look like 'package.module:function'")
    sys.path.insert(0, str(Path.cwd()))
    return getattr(importlib.import_module(module_name), function_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evidence-evals")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="evaluate a system on a dataset")
    run.add_argument("--dataset", required=True)
    run.add_argument("--system", required=True, help="module:function taking the input text and returning the output text")
    run.add_argument("--repeats", type=int, default=1)
    run.add_argument("--min-pass", type=float, default=1.0, help="minimum pass rate (0 to 1), default 1.0")
    run.add_argument("--baseline", help="JSON report from an earlier run; regressions fail the run")
    run.add_argument("--json-out", help="write the JSON report to this file")
    args = parser.parse_args(argv)

    report = evaluate(_load_system(args.system), load_cases(args.dataset), repeats=args.repeats)
    comparison = None
    if args.baseline:
        comparison = compare_to_baseline(report, json.loads(Path(args.baseline).read_text(encoding="utf-8")))
    print(to_markdown(report, comparison))
    if args.json_out:
        Path(args.json_out).write_text(report.to_json() + "\n", encoding="utf-8")
    failed = report.pass_rate < args.min_pass or bool(comparison and comparison["regressions"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
