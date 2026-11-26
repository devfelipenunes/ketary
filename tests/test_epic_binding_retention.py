import gc
import weakref
import numpy as np
import pytest
import ketary as q
from ketary import _ergonomics
from qiskit.quantum_info import Statevector

def test_hessian_releases_disposable_shifts_after_evaluation(monkeypatch):
    p=q.Circuit.parameter("p")
    c=q.Circuit.symbolic(2).ry(p,0).cx(0,1).rz(p,1)
    created=[];seen=[]
    original_shift=_ergonomics._shifted_bound_circuit
    original_run=q.Circuit.run
    def shift(*args,**kwargs):
        got=original_shift(*args,**kwargs)
        created.append(weakref.ref(got))
        return got
    def run(self,*args,**kwargs):
        seen.append(sum(ref() is not None for ref in created))
        return original_run(self,*args,**kwargs)
    monkeypatch.setattr(_ergonomics,"_shifted_bound_circuit",shift)
    monkeypatch.setattr(q.Circuit,"run",run)
    t=.43
    h=c.expectation_hessian({p:t},[q.Z(0)])
    np.testing.assert_allclose(h,[[[-np.cos(t)]]],atol=1e-9,rtol=0)
    assert len(seen)>1 and seen==list(range(len(seen),0,-1))
    gc.collect()
    assert all(ref() is None for ref in created)

def test_sweep_names_keep_explicit_order():
    a,b=q.Circuit.parameter_vector("p",2)
    c=q.Circuit.symbolic(2).ry(a+2*b,0).rz(b,1).cx(0,1)
    plan=c.sweep(**{b.name:[.7,.3],a.name:[.2,-.4]})
    assert plan.bindings==({b.name:.7,a.name:.2},{b.name:.3,a.name:-.4})
    for got,values in zip(plan.run(),({a:.2,b:.7},{a:-.4,b:.3}),strict=True):
        expected=Statevector.from_instruction(c.to_qiskit().assign_parameters(values))
        np.testing.assert_allclose(got.math.statevector(),expected.data,atol=1e-9,rtol=0)
