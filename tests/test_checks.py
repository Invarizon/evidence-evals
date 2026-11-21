import pytest

from evidence_evals.checks import run_checks
from evidence_evals.dataset import Case


def case(checks, sources=None):
    return Case(id="c", input="q", checks=checks, sources=sources or {})


def verdict(output, checks, sources=None):
    return [r.passed for r in run_checks(output, case(checks, sources))]


def test_contains_all_is_case_insensitive_by_default():
    assert verdict("Within 30 DAYS", [{"type": "contains_all", "terms": ["30 days"]}]) == [True]


def test_contains_all_case_sensitive_option():
    assert verdict("within 30 days", [{"type": "contains_all", "terms": ["30 DAYS"], "case_sensitive": True}]) == [False]


def test_contains_none_flags_forbidden_terms():
    assert verdict("the password is x", [{"type": "contains_none", "terms": ["password is"]}]) == [False]


def test_exact_ignores_surrounding_whitespace():
    assert verdict("  42 \n", [{"type": "exact", "value": "42"}]) == [True]


def test_regex():
    assert verdict("Order #1234", [{"type": "regex", "pattern": r"#\d{4}"}]) == [True]
    assert verdict("Order", [{"type": "regex", "pattern": r"#\d{4}"}]) == [False]


def test_length_between():
    assert verdict("one two three", [{"type": "length_between", "min_words": 2, "max_words": 3}]) == [True]
    assert verdict("one", [{"type": "length_between", "min_words": 2}]) == [False]


def test_cites_source_and_validity():
    sources = {"policy-1": "text"}
    assert verdict("Yes [policy-1].", [{"type": "cites_source"}, {"type": "citations_valid"}], sources) == [True, True]
    assert verdict("Yes [policy-9].", [{"type": "citations_valid"}], sources) == [False]
    assert verdict("Yes.", [{"type": "cites_source"}], sources) == [False]


def test_grounded_numbers_rejects_invented_numbers():
    sources = {"s": "Refunds within 30 days."}
    assert verdict("30 days", [{"type": "grounded_numbers"}], sources) == [True]
    assert verdict("45 days", [{"type": "grounded_numbers"}], sources) == [False]


def test_json_valid_with_required_keys():
    assert verdict('{"a": 1}', [{"type": "json_valid", "required_keys": ["a"]}]) == [True]
    assert verdict('{"a": 1}', [{"type": "json_valid", "required_keys": ["b"]}]) == [False]
    assert verdict("not json", [{"type": "json_valid"}]) == [False]


def test_refuses():
    assert verdict("I cannot help with that", [{"type": "refuses"}]) == [True]
    assert verdict("Sure, here you go", [{"type": "refuses"}]) == [False]


def test_unknown_check_raises_with_helpful_message():
    with pytest.raises(ValueError, match="unknown check"):
        run_checks("x", case([{"type": "nope"}]))


def test_grounded_numbers_ignores_numbers_in_citation_markers():
    sources = {"policy-1": "Refunds within 30 days."}
    assert verdict("30 days [policy-1]", [{"type": "grounded_numbers"}], sources) == [True]
