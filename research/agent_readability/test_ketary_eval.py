import pytest
from ketary_eval import CASES, FRAMEWORKS, grade, reference, prompt, compare_syntax

@pytest.mark.parametrize("case",CASES,ids=lambda c:c["id"])
@pytest.mark.parametrize("framework",FRAMEWORKS)
def test_calibration_and_mutants(case,framework):
    assert grade(case,framework,reference(case,framework))["status"]=="PASS"
    assert grade(case,framework,reference(case,framework,True))["status"]=="FAIL"

def test_no_execution_and_framework_enforcement():
    case=CASES[0]
    assert grade(case,"ketary",{"code":"import os\nos.system('echo NEVER')"})["status"]=="UNSUPPORTED"
    assert grade(case,"ketary",reference(case,"candidate"))["status"]=="FAIL"
    assert grade(case,"ketary",reference(case,"qiskit"))["status"]=="FAIL"
    assert grade(case,"ketary",{"code":None})["status"]=="INVALID"

def test_prompt_separation():
    for case in CASES:
        p=prompt(case,"ketary")
        assert not set(p)&{"answer","wrong","gates","mutant"}
    assert compare_syntax()["totals"]["candidate"]<compare_syntax()["totals"]["ketary"]
