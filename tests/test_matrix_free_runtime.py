"""Installed streamed variance vs independent oracle and previous native path."""
from itertools import product
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import XGate,YGate,ZGate

def previous(r,H):
    gates={"X":XGate(),"Y":YGate(),"Z":ZGate()}
    state=r.math.statevector();state/=np.linalg.norm(state)
    result=np.zeros_like(state)
    for label,coefficient in H.to_dict(r.num_qubits).items():
        term=Statevector(state)
        for wire,axis in enumerate(reversed(label)):
            if axis!="I":term=term.evolve(gates[axis],qargs=[wire])
        result+=coefficient*term.data
    delta=result-np.vdot(state,result)*state
    return np.vdot(delta,delta).real

@pytest.mark.parametrize("label",["".join(a) for a in product("IXYZ",repeat=2)])
@pytest.mark.parametrize("minimal",[True,False])
def test_public_variance_matches_native_and_dense(label,minimal):
    v=np.array([1,2j,3+1j,-4-2j],complex);v/=np.linalg.norm(v)
    r=q.Result(v);H=q.Observable({label:.7})+q.Observable({"IZ":-.31,"II":.9})
    matrix=H.to_qiskit(2).to_matrix();hv=matrix@v
    delta=hv-np.vdot(v,hv)*v
    expected=float(np.vdot(delta,delta).real)
    budget=64*len(v) if minimal else 64*1024**2
    assert r.math.observable_variance_streamed(H,max_bytes=budget)==pytest.approx(expected,abs=1e-11)
    assert previous(r,H)==pytest.approx(expected,abs=1e-11)
    np.testing.assert_array_equal(r.math.statevector(),v)

@pytest.mark.parametrize("n",[1,8,12])
def test_budget_compatibility_and_preflight(n):
    r=q.Circuit(n).h(0).run();H=q.Z(0)+.7*q.I()
    assert r.math.observable_variance_streamed(H,max_bytes=64*(1<<n))==pytest.approx(1.,abs=1e-11)
    with pytest.raises(q.ResourceLimit):r.math.observable_variance_streamed(H,max_bytes=64*(1<<n)-1)
    with pytest.raises(q.ResourceLimit):r.math.observable_variance_streamed(H,max_work=1)

def test_no_dense_or_native_per_wire_when_chunk_fits(monkeypatch):
    r=q.bell().run();H=q.Observable({"XX":.7,"ZZ":.3})
    monkeypatch.setattr(Statevector,"evolve",lambda *a,**k:pytest.fail("per-wire path used"))
    assert r.math.variance(H)==pytest.approx(0.,abs=1e-12)
