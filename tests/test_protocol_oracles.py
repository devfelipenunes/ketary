"""Bounded protocol qualification against native Qiskit and analytic predictions.

Refs #297 #108. Ideal coherent circuits and measured Aer protocols are
distinct. Statistical tomography is not a full channel proof.
"""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

STATES = [(0., 0.), (np.pi, 0.), (np.pi/2, 0.), (np.pi/2, np.pi/2), (.83, -1.17)]
SHOTS = 2048
SEED = 29701


def prepare(c, theta, phi):
    c.ry(theta, 0)
    c.rz(phi, 0)
    return c


def coherent_sdk(theta, phi):
    c = prepare(q.Circuit(3), theta, phi)
    return c.h(1).cx(1, 2).cx(0, 1).h(0).cx(1, 2).cz(0, 2)


def coherent_native(theta, phi):
    c = prepare(QuantumCircuit(3), theta, phi)
    c.h(1); c.cx(1, 2); c.cx(0, 1); c.h(0); c.cx(1, 2); c.cz(0, 2)
    return c


def input_state(theta, phi):
    return np.array([np.exp(-.5j*phi)*np.cos(theta/2),
                     np.exp(.5j*phi)*np.sin(theta/2)])


@pytest.mark.parametrize("theta,phi", STATES)
def test_coherent_teleportation(theta, phi):
    # Deferred measurement, not an operational classical communication claim.
    v = input_state(theta, phi)
    expected = np.kron(v, np.ones(4)/2)
    sdk = coherent_sdk(theta, phi).run()
    native = Statevector.from_instruction(coherent_native(theta, phi)).data
    np.testing.assert_allclose(sdk.math.statevector(), expected, atol=1e-9, rtol=0)
    np.testing.assert_allclose(native, expected, atol=1e-9, rtol=0)
    np.testing.assert_allclose(sdk.math.density_matrix([2]), np.outer(v, v.conj()), atol=1e-9, rtol=0)


def sdk_dense(a, b):
    c = q.Circuit.classical(2, 2).h(0).cx(0, 1)
    if a:
        c.z(0)
    if b:
        c.x(0)
    return c.cx(0, 1).h(0).measure(0, 0).measure(1, 1)


def native_dense(a, b):
    c = QuantumCircuit(2, 2)
    c.h(0); c.cx(0, 1)
    if a:
        c.z(0)
    if b:
        c.x(0)
    c.cx(0, 1); c.h(0); c.measure(0, 0); c.measure(1, 1)
    return c


def measured_sdk(theta, phi, axis):
    c = prepare(q.Circuit.classical(3, 3), theta, phi)
    c.h(1).cx(1, 2).cx(0, 1).h(0).measure(0, 0).measure(1, 1)
    c.if_x(2, 1).if_z(2, 0)
    if axis == "Y":
        c.sdg(2)
    if axis in ("X", "Y"):
        c.h(2)
    return c.measure(2, 2)


def measured_native(theta, phi, axis):
    c = prepare(QuantumCircuit(3, 3), theta, phi)
    c.h(1); c.cx(1, 2); c.cx(0, 1); c.h(0)
    c.measure(0, 0); c.measure(1, 1)
    with c.if_test((c.clbits[1], 1)):
        c.x(2)
    with c.if_test((c.clbits[0], 1)):
        c.z(2)
    if axis == "Y":
        c.sdg(2)
    if axis in ("X", "Y"):
        c.h(2)
    c.measure(2, 2)
    return c


def native_counts(c):
    aer = pytest.importorskip("qiskit_aer")
    return aer.AerSimulator().run(c, shots=SHOTS, seed_simulator=SEED).result().get_counts()


@pytest.mark.parametrize("a,b", [(0,0),(0,1),(1,0),(1,1)])
def test_measured_superdense_complete_messages(a, b):
    pytest.importorskip("qiskit_aer")
    expected = {f"{b}{a}": SHOTS}
    assert sdk_dense(a,b).run_shots(shots=SHOTS, seed=SEED).counts == expected
    assert native_counts(native_dense(a,b)) == expected


@pytest.mark.parametrize("theta,phi", STATES)
@pytest.mark.parametrize("axis", ["X", "Y", "Z"])
def test_measured_teleportation_tomography(theta, phi, axis):
    pytest.importorskip("qiskit_aer")
    expected = {"X": np.sin(theta)*np.cos(phi),
                "Y": np.sin(theta)*np.sin(phi), "Z": np.cos(theta)}[axis]
    s = measured_sdk(theta,phi,axis).run_shots(shots=SHOTS,seed=SEED).counts
    n = native_counts(measured_native(theta,phi,axis))
    for counts in (s,n):
        assert sum(counts.values()) == SHOTS
        # Bob's bit is the most significant bit in this full-register label.
        observed = sum((1 if label[0]=="0" else -1)*count for label,count in counts.items())/SHOTS
        assert abs(observed-expected) < .13
        # Bell outcomes are uniform irrespective of the input.
        for pair in ("00","01","10","11"):
            fraction = sum(v for k,v in counts.items() if k[1:]==pair)/SHOTS
            assert abs(fraction-.25) < .07
