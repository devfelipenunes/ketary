"""Composition transaction tests, including actual parameter-table rollback."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from research.symbolic_composition_cost import evaluate

@pytest.mark.parametrize("phase_only",[False,True])
@pytest.mark.parametrize("fail_at",[1,2])
def test_symbolic_composition_rolls_back_all_placements(phase_only,fail_at,monkeypatch):
    p,r=q.Circuit.parameter("p"),q.Circuit.parameter("r")
    c=q.Circuit.symbolic(3).h(0)
    if phase_only:c.evolve(q.I(),time=p)
    else:c.ry(p,0)
    c.register("w",[2,0])
    block=q.Circuit.symbolic(2).ry(p+r,1).cx(1,0).evolve(q.I(),time=r)
    before=c.to_qiskit();source=block.to_qiskit();method=QuantumCircuit.compose;calls=0
    def fail(self,*a,**kw):
        nonlocal calls
        out=method(self,*a,**kw);calls+=1
        if calls==fail_at:raise RuntimeError("after native composition")
        return out
    with monkeypatch.context() as patch:
        patch.setattr(QuantumCircuit,"compose",fail)
        with pytest.raises(RuntimeError):c.apply_each(block,placements=[(2,0),(1,2)])
    assert c.to_qiskit()==before and c.parameters==(p,)
    assert block.to_qiskit()==source and c.registers=={"w":(2,0)}
    c.apply(block,wires=[2,0]);before.compose(source,qubits=[2,0],inplace=True)
    np.testing.assert_allclose(Operator(c.bind({p:.2,r:-.4}).to_qiskit()).data,Operator(before.assign_parameters({p:.2,r:-.4})).data,atol=1e-9,rtol=0)

def test_symbolic_self_application_uses_fixed_source():
    p=q.Circuit.parameter("p");c=q.Circuit.symbolic(2).ry(p,0).cx(0,1).evolve(q.I(),time=p)
    raw=c.to_qiskit();expected=raw.copy()
    for _ in range(3):expected.compose(raw,qubits=[1,0],inplace=True)
    c.apply(c,wires=[1,0],times=3)
    assert c.to_qiskit()==expected and c.parameters==(p,)
    np.testing.assert_allclose(Operator(c.bind({p:.3}).to_qiskit()).data,Operator(expected.assign_parameters({p:.3})).data,rtol=0,atol=1e-9)

def test_checkpoint_survives_composition_failure_and_collision(monkeypatch):
    p=q.Circuit.parameter("p");c=q.Circuit.symbolic(3).h(0).checkpoint("start")
    block=q.Circuit.symbolic(2).ry(p,0).evolve(q.I(),time=p)
    before=c.to_qiskit();method=QuantumCircuit.compose
    def fail(self,*a,**kw):
        method(self,*a,**kw);raise RuntimeError("partial")
    with monkeypatch.context() as patch:
        patch.setattr(QuantumCircuit,"compose",fail)
        with pytest.raises(RuntimeError):c.apply(block,wires=[1,2])
    assert c.checkpoints=={"start":1} and c.to_qiskit()==before and not c.parameters
    c.apply(block,wires=[1,2])
    assert c.checkpoints=={}
    other=q.Circuit.symbolic(2).ry(q.Circuit.parameter("p"),0)
    current=c.to_qiskit()
    with pytest.raises(ValueError):c.apply(other,wires=[1,2])
    assert c.to_qiskit()==current

@pytest.mark.parametrize("n,count",[(4,4),(8,16),(12,4)])
def test_composition_cost(n,count):
    row=evaluate(n,count,reps=2)
    assert all(len(v["raw_ms"])==2 for v in row["stages"].values())
