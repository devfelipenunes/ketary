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

def test_sequence_constraints_and_conditions():
    from ketary_eval import source
    case=next(c for c in CASES if c["id"]=="G03")
    # Identity by a different pair is mathematically valid but not this task.
    assert grade(case,"candidate",{"code":source("candidate",1,[("rx",.2,0),("rx",-.2,0)])})["status"]=="FAIL"
    assert "api" not in prompt(case,"ketary","none")
    assert "context" not in prompt(case,"ketary","none")
    assert "api" in prompt(case,"ketary","card")
    assert "reference" in prompt(case,"ketary","reference")

def test_independent_comprehension_oracles():
    import numpy as np
    from qiskit.quantum_info import Statevector
    from ketary_eval import native
    by={c["id"]:c for c in CASES}
    c=by["C01"]; qc=native(c["n"],c["source"])
    assert [[x.operation.name,[qc.find_bit(w).index for w in x.qubits]] for x in qc.data]==c["answer"]
    c=by["C02"]; a=Statevector.from_instruction(native(2,[("h",0),("cx",0,1)]))
    b=Statevector.from_instruction(native(2,c["source"]))
    assert [bool(np.allclose(a.probabilities(),b.probabilities())),bool(a.equiv(b))]==c["answer"]
    c=by["C03"]; p=Statevector.from_instruction(native(3,c["source"])).probabilities_dict()
    assert max(p,key=p.get)==c["answer"]
    c=by["D01"]; actual=c["source"]; ref=[("h",0),("cx",0,1),("x",0)]
    first=next(i for i in range(1,4) if not Statevector.from_instruction(native(2,actual[:i])).equiv(Statevector.from_instruction(native(2,ref[:i]))))
    assert [first,actual[first-1][0]]==c["answer"]
