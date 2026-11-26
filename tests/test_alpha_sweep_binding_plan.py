"""Sweep optimization must preserve numerical, phase and ownership contracts."""
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator
from ketary._adapter import _bound_validation_indices

@pytest.mark.parametrize("dense",[False,True])
def test_ordered_sweep_matches_full_scan(dense):
    a,b=q.Circuit.parameter_vector("theta",2)
    c=q.Circuit.symbolic(3)
    for _ in range(12):
        c.h(0).cx(0,2)
        if dense:c.ry(a+b,range(3))
    c.rz(b,0).ry(a-b,2)
    raw=c.to_qiskit()
    raw.global_phase=.4*a-.2*b
    c=q.Circuit.from_symbolic(raw)
    plan=_bound_validation_indices(c._qc)
    assert (plan is None)==dense
    values=[(.21,-.6),(.83,.09),(-.37,.55)]
    # Deliberately present names in reversed native order.
    sweep=c.sweep(**{b.name:[y for x,y in values],a.name:[x for x,y in values]})
    for (x,y),out in zip(values,sweep._payloads,strict=True):
        expected=c.bind({a:x,b:y})
        np.testing.assert_allclose(Operator(out.to_qiskit()).data,Operator(expected.to_qiskit()).data,atol=1e-9,rtol=0)
    c.x(1)
    for (x,y),out in zip(values,sweep._payloads,strict=True):
        expected=raw.assign_parameters({a:x,b:y})
        np.testing.assert_allclose(Operator(out.to_qiskit()).data,Operator(expected).data,atol=1e-9,rtol=0)

def test_sparse_plan_checks_every_evaluated_value():
    a=q.Circuit.parameter("a")
    c=q.Circuit.symbolic(2)
    for _ in range(20):c.h(0).cx(0,1)
    c.ry(a*1e200,1)
    with pytest.raises(ValueError):
        c.sweep_rows([(1e-200,),(1e200,)])

def test_sparse_phase_only_and_ownership():
    a=q.Circuit.parameter("a")
    c=q.Circuit.symbolic(2).h(0).cx(0,1)
    raw=c.to_qiskit();raw.global_phase=a
    c=q.Circuit.from_symbolic(raw)
    assert _bound_validation_indices(c._qc)==()
    plan=c.sweep_rows([(.1,),(.7,)])
    for angle,out in zip((.1,.7),plan._payloads,strict=True):
        np.testing.assert_allclose(Operator(out.to_qiskit()).data,Operator(raw.assign_parameters({a:angle})).data,atol=1e-9,rtol=0)


def test_sparse_path_still_validates_each_assignment(monkeypatch):
    from ketary import _adapter
    p=q.Circuit.parameter("p")
    c=q.Circuit.symbolic(2).h(0).cx(0,1).h(0).ry(p,1)
    seen=[];original=_adapter._validate_bound_values
    def check(raw,indices=None):
        seen.append((raw,indices))
        original(raw,indices)
    monkeypatch.setattr(_adapter,"_validate_bound_values",check)
    c.sweep_rows([[.2],[.4]])
    assert len(seen)==2 and seen[0][0] is not seen[1][0]
    assert [indices for _,indices in seen]==[(3,),(3,)]
    assert all(not raw.parameters for raw,_ in seen)


def test_dense_path_preserves_original_mapping_assignment(monkeypatch):
    p=q.Circuit.parameter("p")
    c=q.Circuit.symbolic(2).ry(p,[0,1]).rz(p,0)
    original=q.Circuit._bind_numeric
    seen=[]
    def spy(self,bindings):
        seen.append(bindings)
        return original(self,bindings)
    monkeypatch.setattr(q.Circuit,"_bind_numeric",spy)
    c.sweep_rows([[.2],[.4]])
    assert seen==[{p:.2},{p:.4}]
