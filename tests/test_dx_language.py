import json
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("gate,params",[("h",()),("x",()),("y",()),("z",()),("s",()),("sdg",()),("t",()),("tdg",()),("sx",()),("sxdg",()),("rx",(.2,)),("ry",(.3,)),("rz",(.4,)),("p",(.5,)),("u",(.1,.2,.3))])
def test_batch_matches_native_operator(gate,params):
    c=q.Circuit(4)
    b=QuantumCircuit(4)
    assert getattr(c,gate)(*params,[3,0,2]) is c
    for w in (3,0,2):
        getattr(b,gate)(*params,w)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(b).data,atol=1e-12,rtol=0)
    before=c.to_json()
    for bad in ([0,0],[0,4],[],{0,1},"0",[True,1]):
        with pytest.raises(ValueError):
            getattr(c,gate)(*params,bad)
        assert c.to_json()==before

def test_apply_and_reversible_composition():
    block=q.bell()
    native=block.to_qiskit()
    native.global_phase=.31
    block=q.from_qiskit(native)
    c=q.Circuit(4).h(1)
    expected=c.compose(block,wires=[3,0])
    assert c.apply(block,wires=[3,0]) is c
    assert c.test.equivalent(expected).status=="PASS"
    before=c.to_json()
    with pytest.raises(ValueError):
        c.apply(block,wires=[0,0])
    assert c.to_json()==before
    compute=q.Circuit(2).cx(0,1)
    action=q.Circuit(1).z(0)
    expected=c.compose(compute,wires=[0,1]).compose(action,wires=[1]).compose(compute.inverse(),wires=[0,1])
    assert c.compute_action_uncompute(compute,action,compute_wires=[0,1],action_wires=[1]) is c
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(expected.to_qiskit()).data,atol=1e-12)
    assert q.Circuit.from_json(c.to_json()).test.equivalent(c).status=="PASS"

def test_named_annotations_lifecycle():
    c=q.Circuit(4)
    wires=c.register("pair",[3,0])
    assert wires==(3,0)
    c.apply(q.bell(),wires=wires).checkpoint("entangled")
    contract=c.contract(expectations={"XIIX":1})
    c.z(0).checkpoint("phase")
    report=c.debug.verify_checkpoints({"entangled":contract,"phase":contract})
    assert report.status=="FAIL" and report["first_nonpass"]==3
    assert c.copy().registers==c.registers and c.copy().checkpoints==c.checkpoints
    assert c.optimize().registers=={} and c.optimize().checkpoints=={}
    assert q.Circuit.from_json(c.to_json()).checkpoints=={}
    with pytest.raises(ValueError):
        c.register("pair",[1])
    with pytest.raises(ValueError):
        c.debug.verify_checkpoints({"unknown":contract})
    with pytest.raises(ValueError):
        c.debug.verify_checkpoints({"entangled":contract,2:contract})
    native=q.Circuit(1).to_qiskit()
    native.global_phase=.3
    c.apply(q.from_qiskit(native),wires=[1])
    assert c.checkpoints=={} and c.registers=={"pair":(3,0)}

def test_local_pauli_and_reports(monkeypatch):
    a=q.bell()
    b=a.copy().z(0)
    r=a.run()
    assert r.math.expectation({0:"X",1:"X"})==pytest.approx(1)
    assert r.math.variance({0:"X"})==pytest.approx(1)
    assert r.math.expectation({})==pytest.approx(1)
    for bad in ({2:"X"},{0:"A"},{True:"Z"}):
        with pytest.raises(ValueError):
            r.math.expectation(bad)
    assert r.test.expectations({"XX":1,"ZZ":1}).status=="PASS"
    report=b.test.compare(a)
    assert isinstance(report,q.ComparisonReport)
    assert report.status==report["status"]=="FAIL"
    evidence=report.evidence
    assert evidence is not None and evidence.reproduce()["reproduced"]
    assert report.to_dict()==json.loads(json.dumps(report))
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("hidden simulation"))
    assert report.evidence.to_dict()==report["evidence"]
    assert json.loads(report.render())["status"]=="FAIL"
    with pytest.raises(AssertionError):
        report.require()

def test_named_sweep_is_explicit_and_bounded(monkeypatch):
    p=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(1).ry(p,[0])
    assert c.bind(theta=.5).test.equivalent(c.bind({p:.5})).status=="PASS"
    orig=q.Circuit.run
    calls=[]
    def run(self,*a,**k):
        calls.append(1)
        return orig(self,*a,**k)
    monkeypatch.setattr(q.Circuit,"run",run)
    plan=c.sweep(theta=[0,np.pi])
    c.x(0)
    assert calls==[]
    with pytest.raises(q.ResourceLimit):
        plan.run(max_bytes=1)
    assert calls==[]
    assert plan.bindings==({"theta":0.},{"theta":np.pi})
    first,second=plan.run()
    assert first.math.probability("0")==pytest.approx(1)
    assert second.math.probability("1")==pytest.approx(1)
    assert len(calls)==2
    with pytest.raises(ValueError):
        c.bind({p:0},theta=0)
    with pytest.raises(q.ResourceLimit):
        c.sweep(theta=range(33))

def test_inconclusive_typed_report():
    report=q.Circuit(1).test.compare(q.Circuit(1),complete=False)
    assert report.status=="INCONCLUSIVE" and report.evidence is None
    with pytest.raises(AssertionError):
        report.require()
