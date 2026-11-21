import json
from pathlib import Path

import pytest

from evidence_evals import compare_to_baseline, evaluate, load_cases, to_markdown
from evidence_evals.cli import main
from evidence_evals.dataset import Case

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_example_dataset_passes_with_demo_system():
    from examples.demo_system import answer

    report = evaluate(answer, load_cases(EXAMPLES / "cases.jsonl"), repeats=3)
    assert report.passed == report.total == 4
    assert report.unstable == []


def test_flaky_system_is_detected_by_repeats():
    calls = {"n": 0}

    def flaky(_: str) -> str:
        calls["n"] += 1
        return "ok" if calls["n"] % 2 else "bad"

    cases = [Case(id="a", input="x", checks=[{"type": "contains_all", "terms": ["ok"]}])]
    report = evaluate(flaky, cases, repeats=4)
    assert report.passed == 0  # a case passes only if every run passes
    assert report.unstable == ["a"]
    assert report.results[0].pass_rate == 0.5


def test_baseline_comparison_finds_regressions_and_fixes():
    cases = [
        Case(id="stays", input="x", checks=[{"type": "contains_all", "terms": ["a"]}]),
        Case(id="breaks", input="x", checks=[{"type": "contains_all", "terms": ["a"]}]),
        Case(id="gets-fixed", input="x", checks=[{"type": "contains_all", "terms": ["zzz"]}]),
    ]
    baseline = {"cases": {"stays": {"passed": True}, "breaks": {"passed": True}, "gets-fixed": {"passed": False}, "gone": {"passed": True}}}
    report = evaluate(lambda _: "a", [cases[0], Case(id="breaks", input="x", checks=[{"type": "contains_all", "terms": ["b"]}]), Case(id="gets-fixed", input="x", checks=[{"type": "contains_all", "terms": ["a"]}])])
    result = compare_to_baseline(report, baseline)
    assert result == {"regressions": ["breaks"], "fixed": ["gets-fixed"], "new": [], "removed": ["gone"]}
    assert "breaks" in to_markdown(report, result)


def test_load_cases_validates_input(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"id": "a", "input": "x"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="missing field 'checks'"):
        load_cases(bad)
    dup = tmp_path / "dup.jsonl"
    dup.write_text('{"id":"a","input":"x","checks":[{"type":"exact","value":"1"}]}\n{"id":"a","input":"y","checks":[{"type":"exact","value":"1"}]}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate case id"):
        load_cases(dup)


def test_cli_exit_codes_and_json_report(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(EXAMPLES.parent)
    out = tmp_path / "report.json"
    code = main(["run", "--dataset", "examples/cases.jsonl", "--system", "examples.demo_system:answer", "--repeats", "2", "--json-out", str(out)])
    assert code == 0
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["passed"] == saved["total"] == 4
    # the saved report works as a baseline, and a stricter bar fails the run
    code = main(["run", "--dataset", "examples/cases.jsonl", "--system", "examples.demo_system:answer", "--baseline", str(out)])
    assert code == 0
    failing = tmp_path / "failing.jsonl"
    failing.write_text('{"id":"x","input":"refund","checks":[{"type":"contains_all","terms":["impossible"]}]}\n', encoding="utf-8")
    assert main(["run", "--dataset", str(failing), "--system", "examples.demo_system:answer"]) == 1
    capsys.readouterr()
