"""Injected partial composition failure: rollback must preserve native state (#123)."""
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
import numpy as np

@pytest.mark.parametrize("symbolic",[False,True])
@pytest.mark.parametrize("fail_at",[1,2])
def test_partial_native_compose_rollback(monkeypatch,symbolic,fail_at):
    p=Parameter("theta")
    c=q.Circuit.symbolic(3).rx(p,0) if symbolic else q.Circuit(3).h(0)
    c.checkpoint("prefix") if not symbolic else None
    block=q.Circuit.symbolic(2).ry(p,0).cx(0,1) if symbolic else q.Circuit(2).h(0).cx(0,1).evolve(q.I(),time=.31)
    before=c.to_qiskit()
    source=block.to_qiskit()
    annotations=dict(getattr(c,"_named_checkpoints",{}))
    original=QuantumCircuit.compose
    calls=0
    def fail_after_mutation(self,*args,**kwargs):
        nonlocal calls
        result=original(self,*args,**kwargs)
        if kwargs.get("inplace"):
            calls+=1
            if calls==fail_at:
                raise RuntimeError("injected after native compose")
        return result
    monkeypatch.setattr(QuantumCircuit,"compose",fail_after_mutation)
    with pytest.raises(RuntimeError,match="injected after native compose"):
        c.apply(block,wires=[1,2],times=2)
    assert calls==fail_at
    assert c.to_qiskit()==before
    assert block.to_qiskit()==source
    assert dict(getattr(c,"_named_checkpoints",{}))==annotations
    assert list(c.to_qiskit().parameters)==list(before.parameters)

@pytest.mark.parametrize("coef",[float("nan"),float("inf"),-float("inf")])
def test_nonfinite_observable_never_reaches_evolution(coef):
    c=q.Circuit(1).h(0)
    before=c.to_qiskit()
    with pytest.raises(ValueError):
        c.evolve(q.Observable({"X":coef}),time=.3)
    assert c.to_qiskit()==before
