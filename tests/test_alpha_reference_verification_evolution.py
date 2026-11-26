"""Held-out authored mathematical cases: strict phase, ordered wires, replay."""
import numpy as np
import pytest
from scipy.linalg import expm
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector
import ketary as q

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)

@pytest.mark.parametrize("t", [-.7, .0, .39])
def test_alpha_commuting_evolution_strict_phase(t):
    # XX and ZZ commute despite overlapping support; identity is global phase.
    H = .4*np.kron(X, X) + .3*np.kron(Z, Z) + .2*np.eye(4)
    obs = .4*(q.X(0) @ q.X(1)) + .3*(q.Z(0) @ q.Z(1)) + .2*q.I()
    sdk = q.Circuit(2).evolve(obs, time=t)
    native = QuantumCircuit(2)
    native.rxx(.8*t, 0, 1)
    native.rzz(.6*t, 0, 1)
    native.global_phase = -.2*t
    expected = expm(-1j*t*H)
    for c in (sdk.to_qiskit(), native):
        np.testing.assert_allclose(Operator(c).data, expected, atol=1e-9, rtol=0)
    initial = np.array([1, 2j, -.3, .4j], complex)
    initial /= np.linalg.norm(initial)
    actual = sdk.run(initial_state=initial)
    np.testing.assert_allclose(actual.math.statevector(), expected @ initial, atol=1e-9, rtol=0)
    energy = float(np.vdot(initial, H @ initial).real)
    q.Contract(2, expectations={obs: energy}).verify(actual).require()

@pytest.mark.parametrize("steps", [2, 4, 8])
def test_alpha_noncommuting_product_formula(steps):
    # Separate the exact physical target from the intended approximate product.
    H = .71*X + .43*Z
    obs = .71*q.X(0) + .43*q.Z(0)
    t = .62
    c = q.Circuit(1)
    with pytest.raises(q.UnsupportedOperation):
        c.evolve(obs, time=t)
    assert len(c.to_qiskit().data) == 0
    sdk = q.Circuit(1).evolve_product(obs, time=t, steps=steps, order=2)
    native = QuantumCircuit(1)
    # Canonical ordering is X then Z; symmetric second-order sequence.
    for _ in range(steps):
        native.rx(.71*t/steps, 0)
        native.rz(.43*t/steps, 0)
        native.rz(.43*t/steps, 0)
        native.rx(.71*t/steps, 0)
    actual = Operator(sdk.to_qiskit()).data
    expected = Operator(native).data
    np.testing.assert_allclose(actual, expected, atol=1e-9, rtol=0)
    exact = expm(-1j*t*H)
    previous = Operator(q.Circuit(1).evolve_product(obs, time=t, steps=steps//2, order=2).to_qiskit()).data
    assert np.linalg.norm(actual-exact) < np.linalg.norm(previous-exact)

@pytest.mark.parametrize("wire", [0, 2])
def test_alpha_phase_defect_replay(wire):
    reference = q.Circuit(3).h(0).cx(0,1).cx(1,2)
    bad = reference.copy().z(wire)
    native = QuantumCircuit(3)
    native.h(0)
    native.cx(0,1)
    native.cx(1,2)
    native.z(wire)
    expected = np.zeros(8, complex)
    expected[[0, 7]] = [1/np.sqrt(2), -1/np.sqrt(2)]
    np.testing.assert_allclose(Statevector.from_instruction(native).data, expected, atol=1e-9, rtol=0)
    np.testing.assert_allclose(bad.run().math.statevector(), expected, atol=1e-9, rtol=0)
    reference.run().test.distribution(bad.run()).require()
    observable = q.X(0) @ q.X(1) @ q.X(2)
    contract = reference.contract(expectations={observable: 1.})
    contract.verify(reference.run()).require()
    assert contract.verify(bad.run()).status == "FAIL"
    report = bad.test.compare(reference, inputs=["000"])
    assert report.status == "FAIL" and report.evidence is not None
    evidence = q.Evidence.from_json(report.evidence.to_json())
    assert evidence.reproduce()["reproduced"]
    corrected = bad.copy().z(wire)
    contract.verify(corrected.run()).require()
    corrected.test.equivalent(reference).require()
