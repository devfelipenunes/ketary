import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from research.composition_suffix_transaction import suffix_transaction,evaluate

@pytest.mark.parametrize("alias",["none","compute","action","both"])
@pytest.mark.parametrize("phase",[0.,.37])
def test_alias_and_phase(alias,phase):
    def fixture():
        c=q.Circuit(3).h(2).cx(2,0).evolve(q.I(),time=.21)
        c.checkpoint("before");c.register("selected",[2,0])
        u=q.Circuit(2).h(0).cx(0,1)
        v=q.Circuit(1).rz(.3,0).evolve(q.I(),time=phase)
        if alias in ("compute","both"):u=c
        if alias in ("action","both"):v=c
        cw=(2,0,1) if u is c else (2,0)
        aw=(1,2,0) if v is c else (0,)
        return c,u,v,cw,aw
    a,u,v,cw,aw=fixture();b,x,y,ci,ai=fixture()
    a.compute_action_uncompute(u,v,compute_wires=cw,action_wires=aw)
    suffix_transaction(b,x,y,ci,ai)
    assert a.to_qiskit()==b.to_qiskit()
    np.testing.assert_allclose(Operator(a.to_qiskit()).data,Operator(b.to_qiskit()).data,atol=1e-9,rtol=0)
    assert a.checkpoints==b.checkpoints and a.registers==b.registers

@pytest.mark.parametrize("fail_at",[1,2,3])
def test_late_failure_restores_prefix_phase_and_annotations(monkeypatch,fail_at):
    c=q.Circuit(3).h(0).evolve(q.I(),time=.13).checkpoint("before")
    u=q.Circuit(2).cx(0,1);v=q.Circuit(1).z(0)
    before=c.to_qiskit();checkpoints=c.checkpoints
    original=QuantumCircuit.compose;calls=[]
    def fail(self,*args,**kwargs):
        calls.append(1)
        result=original(self,*args,**kwargs)
        if len(calls)==fail_at:
            self.x(1);self.global_phase=.77
            raise RuntimeError("injected append failure")
        return result
    monkeypatch.setattr(QuantumCircuit,"compose",fail)
    with pytest.raises(RuntimeError,match="injected"):
        suffix_transaction(c,u,v,(0,2),(2,))
    assert c.to_qiskit()==before and c.checkpoints==checkpoints

def test_invalid_late_mapping_precedes_native_append(monkeypatch):
    c=q.Circuit(3).h(0);u=q.Circuit(2).cx(0,1);v=q.Circuit(1).z(0)
    before=c.to_qiskit()
    monkeypatch.setattr(QuantumCircuit,"compose",lambda *a,**k:pytest.fail("native append before preflight"))
    with pytest.raises(ValueError):suffix_transaction(c,u,v,(0,2),(0,1))
    assert c.to_qiskit()==before

def test_diagnostic_smoke():
    row=evaluate(32,3)
    assert max(row["errors"].values())<=1e-9
