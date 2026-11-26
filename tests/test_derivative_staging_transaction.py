"""Shared derivative staging must keep preflight, native ownership and phase."""
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator
from ketary._ergonomics import _shifted_bound_circuit
from ketary import _ergonomics

@pytest.mark.parametrize("offsets",[(),((0,.3),),((1,-.7),),((0,.2),(1,-.4))])
def test_native_shift_snapshot(offsets):
    c=q.Circuit(2).ry(.4,0).crx(-.5,0,1).evolve(q.I(1),time=.2)
    before=c.to_qiskit()
    raw=c.to_qiskit()
    got=_shifted_bound_circuit(raw,offsets)
    expected=before.copy()
    for i,delta in offsets:
        item=expected.data[i]
        op=item.operation.to_mutable()
        op.params=[float(op.params[0])+delta]
        expected.data[i]=item.replace(operation=op)
    np.testing.assert_allclose(Operator(got.to_qiskit()).data,Operator(expected).data,atol=1e-9,rtol=0)
    assert raw==before and c.to_qiskit()==before
    got.x(0)
    assert raw==before

@pytest.mark.parametrize("method",["expectation_jacobian","expectation_hessian","quantum_geometric_tensor"])
def test_late_staging_fault_before_any_simulation(method,monkeypatch):
    a,b=q.Circuit.parameter_vector("t",2)
    c=q.Circuit.symbolic(2).ry(a+b,0).crx(a*b,0,1)
    before=c.to_qiskit()
    calls=[]
    original=_ergonomics._shifted_bound_circuit
    def fail_second(bound,offsets):
        calls.append(1)
        if len(calls)==2:
            raise ArithmeticError("injected late staging failure")
        return original(bound,offsets)
    monkeypatch.setattr(_ergonomics,"_shifted_bound_circuit",fail_second)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("simulation preceded complete staging"))
    args=({a:.3,b:.7},) if method=="quantum_geometric_tensor" else ({a:.3,b:.7},[q.Z(1)])
    with pytest.raises(ArithmeticError,match="late staging"):
        getattr(c,method)(*args)
    assert len(calls)==2 and c.to_qiskit()==before
