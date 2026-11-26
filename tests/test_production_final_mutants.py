"""Independent regression oracles for the final 28 declared mutations."""
import sys,types
import numpy as np
import pytest
import ketary as q
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Kraus,DensityMatrix,Operator

def test_strict_metadata():
    raw=QuantumCircuit(1,metadata={"x":1})
    raw.h(0)
    with pytest.raises(q.UnsupportedOperation):q.from_qiskit(raw)

def test_full_channel_width():
    with pytest.raises(q.ResourceLimit):q.Circuit(5).run_channel(Kraus([np.eye(32)]))

def test_density_input_preflight(monkeypatch):
    monkeypatch.setattr(DensityMatrix,"evolve",lambda *a,**kw:pytest.fail("invalid density reached evolution"))
    with pytest.raises(ValueError):q.Circuit(1).run_density(DensityMatrix(np.diag([1.2,-.2])))

def test_density_width_preflight(monkeypatch):
    monkeypatch.setattr(DensityMatrix,"from_instruction",lambda *a,**kw:pytest.fail("oversized density reached evolution"))
    with pytest.raises(q.ResourceLimit):q.Circuit(9).run_density()

def test_shot_provenance():
    pytest.importorskip("qiskit_aer")
    result=q.Circuit.classical(2,2).x(0).measure(0,1).measure(1,0).run_shots(shots=8,seed=41)
    assert result.counts=={"10":8}
    assert result.measurements==((2,0,1),(3,1,0))

def forbid_aer(monkeypatch):
    fake=types.ModuleType("qiskit_aer")
    fake.AerSimulator=lambda *a,**kw:pytest.fail("backend reached before preflight")
    monkeypatch.setitem(sys.modules,"qiskit_aer",fake)

def test_shot_cap(monkeypatch):
    forbid_aer(monkeypatch)
    with pytest.raises(q.ResourceLimit):q.Circuit.classical(1,1).measure(0,0).run_shots(shots=10001)

def test_shot_requires_measurement(monkeypatch):
    forbid_aer(monkeypatch)
    with pytest.raises(ValueError):q.Circuit.classical(1,1).run_shots(shots=8)

def test_dense_evolution_sign():
    from scipy.linalg import expm
    H=np.array([[.3,.7],[.7,-.3]])
    c=q.Circuit(1).evolve_exact(.3*q.Z(0)+.7*q.X(0),time=.43)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expm(-1j*.43*H),atol=1e-9,rtol=0)

def test_dense_state_phase():
    v=np.array([1,1j])/np.sqrt(2)
    np.testing.assert_allclose(q.Circuit.prepare_state(v).run().math.statevector(),v,atol=1e-9,rtol=0)

def test_dense_unitary_direction():
    U=np.diag([1,np.exp(.7j)])
    np.testing.assert_allclose(Operator(q.Circuit.from_unitary(U).to_qiskit()).data,U,atol=1e-9,rtol=0)

def test_open_control():
    c=q.Circuit(1).x(0).control(control_state=0)
    assert c.run(initial_state="00").math.probabilities()==pytest.approx({"00":0,"01":0,"10":1,"11":0},abs=1e-9)

def test_synthesis_input_cap(monkeypatch):
    raw=QuantumCircuit(1)
    for _ in range(257):raw.u(0,0,0,0)
    monkeypatch.setattr(qiskit,"transpile",lambda *a,**kw:pytest.fail("compiler reached before preflight"))
    with pytest.raises(q.ResourceLimit):q.Circuit.from_synthesized(raw)

def test_asymmetric_embedding():
    assert q.Observable({"XZ":1}).on([2,0],width=3).to_dict()=={"ZIX":1}

def test_observable_addition():
    assert (q.X(0)+2*q.X(0)).to_dict()=={"X":3.}

def test_overlapping_tensor():
    with pytest.raises(ValueError):q.X(0)@q.Z(0)
