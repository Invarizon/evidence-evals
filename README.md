# evidence-evals

**Deterministic evidence for probabilistic systems.**

A small, dependency-free Python toolkit to evaluate the output of LLMs, RAG pipelines and agents with checks that are fixed in advance and give the same verdict every time. It is built around one idea: a convincing answer is not evidence of a correct answer, so you agree on the rules first and judge the system against them.

It is deliberately small. It is a starting point you can read in ten minutes, not a benchmark suite and not a certification.

## What it does

- **Cases as data**: one JSON object per line, with the checks that define a good answer.
- **Deterministic checks**: `contains_all`, `contains_any`, `contains_none`, `exact`, `regex`, `length_between`, `cites_source`, `citations_valid`, `grounded_numbers`, `json_valid`, `refuses`.
- **Repeat runs** to expose non-determinism: a case only passes if every run passes, and cases with mixed verdicts are reported as unstable.
- **Regression detection** against an earlier report: what passed before and fails now.
- **A CLI and a Robot Framework library**, so the same evidence can run locally, in CI or inside an existing test suite.

## Quick start

```bash
pip install -e ".[dev]"
evidence-evals run \
  --dataset examples/cases.jsonl \
  --system examples.demo_system:answer \
  --repeats 3 \
  --json-out report.json
```

`--system` is any `module:function` that takes the input text and returns the output text. Wrap your model call, RAG pipeline or agent in such a function.

Fail the run on regressions and on a minimum pass rate:

```bash
evidence-evals run --dataset cases.jsonl --system my_app:ask --repeats 3 --baseline report.json --min-pass 0.95
```

## A case

```json
{
  "id": "refund-window",
  "input": "What is the refund window?",
  "sources": {"policy-1": "Refunds are possible within 30 days of purchase."},
  "tags": ["rag"],
  "checks": [
    {"type": "contains_all", "terms": ["30 days"]},
    {"type": "cites_source"},
    {"type": "citations_valid"},
    {"type": "grounded_numbers"}
  ]
}
```

`grounded_numbers` fails if the answer contains a number that does not occur in the provided sources, a cheap and strict guard against invented figures. Numbers inside citation markers such as `[policy-1]` are ignored.

## Robot Framework

```robotframework
*** Settings ***
Library    evidence_evals.robot_library.EvidenceEvals

*** Test Cases ***
Demo system meets the agreed pass rate
    ${rate}=    Run Evaluation    examples/cases.jsonl    examples.demo_system:answer    repeats=3
    Pass Rate Should Be At Least    1.0
    No Unstable Cases
```

## What this is not

- Not a measure of "intelligence" or general model quality.
- Not a replacement for human review of consequential decisions.
- Not exhaustive: deterministic checks catch what you thought to specify. Combine them with representative evaluation sets, adversarial tests and monitoring after go-live.

## Extending

A check is a function `(output, case, params) -> (passed, detail)`. Add it to `CHECKS` in `src/evidence_evals/checks.py` and add a test. Keep checks pure: no network, no randomness.

## Development

```bash
pip install -e ".[dev]"
pytest -q
```

Supports Python 3.9 and newer. MIT licensed.

## In het Nederlands

`evidence-evals` is een kleine bibliotheek om de uitvoer van taalmodellen, RAG en agents te toetsen met vooraf vastgelegde, deterministische controles. Je spreekt eerst af wat een goed antwoord is en toetst het systeem daaraan, in plaats van te vertrouwen op een antwoord dat overtuigend klinkt. Het is een startpunt en geen certificering: combineer het met representatieve evaluatiesets, tegenwerkende tests en monitoring na livegang.

---

Maintained by [Invarizon](https://invarizon.nl).
