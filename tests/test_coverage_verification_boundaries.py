"""Coverage-directed regression oracles: verdicts, boundaries and phase."""
import copy
import hashlib
import json
import sys
import types
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector
from ketary._verification import _json
from ketary._adapter import _append_bound_blocks

def test_lowering_preserves_occupied_spectator_and_phase():
    native=QuantumCircuit(5,global_phase=.319)
    native.mcx([4,0,2],1)
    c=q.from_qiskit(native)
    lowered=c.transpile(basis_gates=["h","x","p","cx"],seed=1101)
    np.testing.assert_allclose(Operator(lowered.to_qiskit()).data,Operator(native).data,atol=1e-9,rtol=0)
    v=np.random.default_rng(1201).normal(size=32)+1j*np.random.default_rng(1202).normal(size=32)
    v/=np.linalg.norm(v)
    np.testing.assert_allclose(lowered.run(initial_state=v).math.statevector(),Statevector(v).evolve(native).data,atol=1e-9,rtol=0)

def test_transpilation_explicitly_disables_clean_input_assumption(monkeypatch):
    import qiskit
    original=qiskit.transpile
    seen=[]
    def wrapper(*args,**kwargs):
        seen.append(kwargs.get("qubits_initially_zero"))
        return original(*args,**kwargs)
    monkeypatch.setattr(qiskit,"transpile",wrapper)
    q.bell().transpile(basis_gates=["h","cx"])
    assert seen==[False]

def witness():
    report=q.Circuit(2).x(0).test.compare(q.Circuit(2),inputs=["00"],complete=False)
    assert report.status=="FAIL"
    return report.evidence

def resign(envelope):
    envelope["sha256"]=hashlib.sha256(_json(envelope["data"]).encode()).hexdigest()
    return envelope

@pytest.mark.parametrize("field,value",[
    ("schema_version",True),("kind","unknown"),("input","0"),
    ("ignore_global_phase",1),("atol",-1),("recorded_distance",3),
    ("recorded_distance",0),("producer",{"ketary":"x"}),
])
def test_evidence_rejects_resigned_invalid_fields(field,value):
    e=witness().to_dict()
    e["data"][field]=value
    with pytest.raises(ValueError):
        q.Evidence.from_json(_json(resign(e)))

def test_evidence_hash_and_duplicate_keys_rejected():
    e=witness().to_dict()
    e["data"]["recorded_distance"]=1.2
    with pytest.raises(ValueError,match="hash"):
        q.Evidence.from_dict(e)
    payload=witness().to_json().replace('"schema_version":1','"schema_version":1,"schema_version":1',1)
    with pytest.raises(ValueError,match="duplicate"):
        q.Evidence.from_json(payload)

def test_evidence_does_not_certify_unreproduced_witness():
    e=witness().to_dict()
    e["data"]["observed"]=e["data"]["reference"]
    artifact=q.Evidence.from_dict(resign(e))
    assert artifact.reproduce()["reproduced"] is False
    result=artifact.minimize()
    assert result["status"]=="INCONCLUSIVE" and result["attempts"]==0

def test_evidence_minimization_budget():
    e=witness()
    with pytest.raises(q.ResourceLimit):e.minimize(max_attempts=129)
    result=e.minimize(max_attempts=1)
    assert result["status"]=="FAIL"
    assert q.Evidence.from_dict(result["evidence"]).reproduce()["reproduced"]

@pytest.mark.parametrize("inputs",[[],["00","00"],["0"],["zz"],["00"]*33])
def test_comparison_invalid_inputs(inputs):
    with pytest.raises(ValueError):
        q.bell().test.compare(q.bell(),inputs=inputs)

def test_selected_input_is_not_operator_equivalence():
    a=q.Circuit(2).z(0);b=q.Circuit(2)
    assert a.test.compare(b,inputs=["00"],complete=False).status=="INCONCLUSIVE"
    assert a.test.compare(b,inputs=["00"],complete=True).status=="FAIL"

def test_complete_unsupported_never_promotes_selected_success():
    a=q.Circuit(9)
    assert a.test.compare(a.copy(),inputs=["0"*9]).status=="INCONCLUSIVE"

@pytest.mark.parametrize("raw,expected",[
    ({"equivalence":"equivalent"},"PASS"),
    ({"equivalence":"equivalent_up_to_global_phase"},"PASS"),
    ({"equivalence":"not_equivalent"},"FAIL"),
    ({"equivalence":"probably_equivalent"},"INCONCLUSIVE"),
    ({"equivalence":None},"INCONCLUSIVE"),(None,"INCONCLUSIVE"),
])
def test_external_verdict_mapping(monkeypatch,raw,expected):
    import importlib.metadata
    mqt=types.ModuleType("mqt")
    mqt.qcec=types.SimpleNamespace(verify_with_hard_timeout=lambda *a,**k:raw)
    monkeypatch.setitem(sys.modules,"mqt",mqt)
    monkeypatch.setattr(importlib.metadata,"version",lambda _: "test-fixture")
    report=q.bell().test.external_equivalence(q.bell())
    assert report.status==expected

@pytest.mark.parametrize("error,expected",[(TimeoutError,"INCONCLUSIVE"),(RuntimeError,"UNSUPPORTED"),(ValueError,"UNSUPPORTED"),(TypeError,"UNSUPPORTED")])
def test_external_backend_exceptions(monkeypatch,error,expected):
    import importlib.metadata
    def fail(*a,**k):raise error("injected")
    mqt=types.ModuleType("mqt")
    mqt.qcec=types.SimpleNamespace(verify_with_hard_timeout=fail)
    monkeypatch.setitem(sys.modules,"mqt",mqt)
    monkeypatch.setattr(importlib.metadata,"version",lambda _: "test-fixture")
    assert q.bell().test.external_equivalence(q.bell()).status==expected

def test_external_rejects_invalid_deadline_and_width():
    with pytest.raises(ValueError):q.bell().test.external_equivalence(q.bell(),deadline=0)
    with pytest.raises(q.ResourceLimit):q.bell().test.external_equivalence(q.Circuit(3))

@pytest.mark.parametrize("counts",[
    (("0",50),("0",50)),(("0",99),),(("2",100),),
    (("0",101),("1",-1)),(("0",True),("1",99)),
])
def test_statistical_rejects_malformed_measured_counts(counts):
    r=q.ShotResult(100,1,1,counts,((1,0,0),))
    contract=q.StatisticalContract(1,probabilities={"0":.5})
    with pytest.raises(ValueError):contract.verify(r)

def test_statistical_iid_verdict_boundaries():
    contract=q.StatisticalContract(1,probabilities={"0":.5},margin=.1)
    def shots(n,zero):
        return q.ShotResult(n,1,1,(("0",zero),("1",n-zero)),((1,0,0),))
    assert contract.verify(shots(10000,5000)).status=="PASS"
    assert contract.verify(shots(10000,10000)).status=="FAIL"
    assert contract.verify(shots(10,5)).status=="INCONCLUSIVE"
    assert contract.verify(q.ShotResult(10,1,1,(("0",10),))).status=="UNSUPPORTED"

def test_bound_native_transaction_rolls_back_after_second_failure(monkeypatch):
    target=QuantumCircuit(3,global_phase=.2);target.h(2)
    block=QuantumCircuit(1,global_phase=.31);block.x(0)
    before=target.copy()
    original=QuantumCircuit.compose
    calls=[]
    def injected(self,*args,**kwargs):
        value=original(self,*args,**kwargs)
        calls.append(1)
        if len(calls)==2:raise RuntimeError("injected post-append failure")
        return value
    monkeypatch.setattr(QuantumCircuit,"compose",injected)
    with pytest.raises(RuntimeError):
        _append_bound_blocks(target,block,((0,),(1,)))
    assert target==before
    np.testing.assert_allclose(Operator(target).data,Operator(before).data,atol=1e-9,rtol=0)
