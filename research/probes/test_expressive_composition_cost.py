import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from research.expressive_composition_cost import workload,_one_staged_copy,evaluate

@pytest.mark.parametrize("alias",[False,True])
@pytest.mark.parametrize("phase",[0.,.4])
def test_staging_reference_and_annotations(alias,phase):
    c,u,_,cw,aw=workload(32,alias)
    v=q.Circuit(1).rz(.37,0).evolve(q.I(),time=phase)
    c.register("pair",[3,0])
    a=c.copy();b=c.copy()
    ua=a if alias else u
    ub=b if alias else u
    a.compute_action_uncompute(ua,v,compute_wires=cw,action_wires=aw)
    _one_staged_copy(b,ub,v,cw,aw)
    np.testing.assert_allclose(Operator(a.to_qiskit()).data,Operator(b.to_qiskit()).data,atol=1e-9,rtol=0)
    assert a.checkpoints==b.checkpoints and a.registers==b.registers=={"pair":(3,0)}
    assert c.checkpoints=={"prefix":32}

def test_staging_failure_is_atomic(monkeypatch):
    c,u,v,cw,aw=workload(32)
    before=c.to_qiskit()
    original=QuantumCircuit.compose
    calls=[]
    def fail(self,*a,**kw):
        calls.append(1)
        if len(calls)==2:
            self.x(0);self.global_phase=.9
            raise RuntimeError("late native failure")
        return original(self,*a,**kw)
    monkeypatch.setattr(QuantumCircuit,"compose",fail)
    with pytest.raises(RuntimeError,match="late native failure"):
        _one_staged_copy(c,u,v,cw,aw)
    assert c.to_qiskit()==before and c.checkpoints=={"prefix":32}

def test_matched_diagnostic_smoke():
    row=evaluate(32,3)
    assert max(row["residual"].values())<=1e-9
    assert all(len(v["raw_ms"])==3 for v in row["variants"].values())
