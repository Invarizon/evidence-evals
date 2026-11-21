*** Settings ***
Library    evidence_evals.robot_library.EvidenceEvals

*** Test Cases ***
Demo system meets the agreed pass rate
    ${rate}=    Run Evaluation    examples/cases.jsonl    examples.demo_system:answer    repeats=3
    Pass Rate Should Be At Least    1.0
    No Unstable Cases
