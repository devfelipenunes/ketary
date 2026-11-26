"""Independent checks for the public v0.3 calibration corpus."""
from collections import Counter
import json

import ketary as q
import numpy as np
import pytest
from qiskit.quantum_info import Operator, Pauli, Statevector

from corpus_v03 import CASES, FRAMEWORKS, TARGET, source_for
from ketary_eval import native, reference
from ketary_eval_v03 import export, grade, grade_packet, prompt
from source_reader import read_source


@pytest.mark.parametrize("case",CASES,ids=lambda c:c["id"])
@pytest.mark.parametrize("framework",FRAMEWORKS)
def test_calibration(case,framework):
    assert grade(case,framework,reference(case,framework))["status"]=="PASS"
    assert grade(case,framework,reference(case,framework,True))["status"]=="FAIL"


@pytest.mark.parametrize("case",[c for c in CASES if "gates" in c],ids=lambda c:c["id"])
def test_actual_sdk_paths(case):
    expected=Operator(native(case["n"],case["gates"])).data
    for framework in ("ketary","candidate"):
        circuit=q.Circuit(case["n"])
        for name,*args in case["gates"]:
            getattr(circuit.gates if framework=="ketary" else circuit,name)(*args)
        np.testing.assert_allclose(Operator(circuit.to_qiskit()).data,expected,atol=1e-9,rtol=0)


@pytest.mark.parametrize("case",[c for c in CASES if c["kind"]=="mathematics"],ids=lambda c:c["id"])
def test_math_oracles(case):
    state=Statevector.from_instruction(native(case["n"],case["source"]))
    actual=(state.expectation_value(Pauli(case["pauli"])).real if "pauli" in case
            else state.probabilities()[0])
    assert actual==pytest.approx(case["answer"],abs=1e-9)
    assert actual!=pytest.approx(case["wrong"],abs=1e-9)


@pytest.mark.parametrize("case",[c for c in CASES if c["kind"]=="comprehension" and not c["family"].startswith("legacy")],ids=lambda c:c["id"])
def test_comprehension_oracles(case):
    qc=native(case["n"],case["source"])
    state=Statevector.from_instruction(qc)
    if case["family"]=="ordered-wires":
        actual=[[x.operation.name,[qc.find_bit(w).index for w in x.qubits]] for x in qc.data]
    elif case["family"]=="phase-vs-distribution":
        ref=Statevector.from_instruction(native(case["n"],case["reference_gates"]))
        actual=[bool(np.allclose(state.probabilities(),ref.probabilities())),bool(state.equiv(ref))]
    else:
        assert max(state.probabilities())==pytest.approx(1,abs=1e-9)
        actual=format(int(np.argmax(state.probabilities())),f"0{case['n']}b")
    assert actual==case["answer"]
    assert actual!=case["wrong"]


@pytest.mark.parametrize("case",[c for c in CASES if c["kind"]=="debugging" and "reference_gates" in c],ids=lambda c:c["id"])
def test_diagnosis_oracles(case):
    obs,ref=case["source"],case["reference_gates"]
    first=next(i for i in range(1,len(obs)+1) if not
        Statevector.from_instruction(native(case["n"],obs[:i])).equiv(
        Statevector.from_instruction(native(case["n"],ref[:i]))))
    assert [first,obs[first-1][0]]==case["answer"]
    a,b=q.Circuit(case["n"]),q.Circuit(case["n"])
    for circuit,ops in ((a,obs),(b,ref)):
        for name,*args in ops:
            getattr(circuit,name)(*args)
    assert a.debug.compare(b).to_dict()["step_index"]==first


@pytest.mark.parametrize("case",[c for c in CASES if c["kind"]=="abstention"],ids=lambda c:c["id"])
@pytest.mark.parametrize("framework",FRAMEWORKS)
def test_abstention_oracle(case,framework):
    assert read_source(source_for(case,framework))["status"]==case["answer"]


def test_corpus_and_prompts():
    assert len(CASES)==180
    assert Counter(c["kind"] for c in CASES)==TARGET
    assert len({c["id"] for c in CASES})==180
    forbidden={"answer","wrong","gates","mutant","intended","reference_gates","family"}
    for framework in FRAMEWORKS:
        for condition in ("none","card","reference"):
            rows=export(framework,condition,42)
            assert len(rows)==180
            assert rows==export(framework,condition,42)
            assert rows!=export(framework,condition,43)
            assert all(not (set(row)&forbidden) for row in rows)
            json.dumps(rows,allow_nan=False)


def test_packet_denominators_and_validation():
    packet={"framework":"candidate","condition":"card","responses":[]}
    out=grade_packet(packet)
    assert out["n"]==180 and out["pass"]==0
    assert sum(x["statuses"]["MISSING"] for x in out["by_kind"].values())==180
    assert out["abstention"]=={"PASS":{"n":10,"correct":0},"UNSUPPORTED":{"n":10,"correct":0}}
    packet["responses"]=[{"id":c["id"],"response":reference(c,"candidate")} for c in CASES]
    assert grade_packet(packet)["pass"]==180
    packet["responses"]=[{"id":"G01","response":{}},{"id":"G01","response":{}}]
    with pytest.raises(ValueError,match="duplicate"):
        grade_packet(packet)


def test_semantic_testing_and_optimization():
    case=next(c for c in CASES if c["kind"]=="testing")
    # A spectator bit does not affect the controlled-X defect.
    answer=[format(int(s,2)|4,"03b") for s in case["answer"]]
    assert grade(case,"candidate",{"answer":answer})["status"]=="PASS"
    assert grade(case,"candidate",{"answer":["0","0"]})["status"]=="INVALID"
    opt=next(c for c in CASES if c["kind"]=="optimization")
    assert "Maximum gate count: 2" in prompt(opt,"candidate")["constraints"]
    assert grade(opt,"candidate",reference(opt,"candidate",True))["reason"]=="operator equivalent but exceeds gate budget"
