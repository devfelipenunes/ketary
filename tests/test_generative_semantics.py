"""Seeded generative and metamorphic tests; Qiskit full operator is oracle."""
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import ketary as q

@pytest.mark.parametrize("seed",range(32))
def test_random_circuits(seed):
    rng=np.random.default_rng(seed)
    n=3
    a=q.Circuit(n)
    b=QuantumCircuit(n)
    for _ in range(12):
        gate=rng.choice(["h","x","y","z","s","t","rx","ry","rz","p","u","cx","cz","cp","crx","rxx","ryy","rzz","ccx","cswap"])
        wires=rng.choice(n,size=3,replace=False).tolist()
        theta=float(rng.uniform(-2,2))
        args=([theta,-theta,.2,wires[0]] if gate=="u" else
              [theta,wires[0]] if gate in ("rx","ry","rz","p") else
              [theta,*wires[:2]] if gate in ("cp","crx","rxx","ryy","rzz") else
              wires if gate in ("ccx","cswap") else wires[:2] if gate in ("cx","cz") else wires[:1])
        getattr(a,gate)(*args)
        getattr(b,gate)(*args)
    expected=Operator(b).data
    np.testing.assert_allclose(Operator(a.to_qiskit()).data,expected,atol=1e-10,rtol=0)
    for c in (q.Circuit.from_json(a.to_json()),a.copy(),a.optimize()):
        np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-10,rtol=0)
    np.testing.assert_allclose(Operator(a.compose(a.inverse()).to_qiskit()).data,np.eye(8),atol=1e-10,rtol=0)
    state=rng.normal(size=8)+1j*rng.normal(size=8)
    state/=np.linalg.norm(state)
    np.testing.assert_allclose(a.run(initial_state=state).math.statevector(),expected@state,atol=1e-10,rtol=0)
