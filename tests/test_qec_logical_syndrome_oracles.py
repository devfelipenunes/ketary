"""Ideal injected-error QEC qualification, refs #296 #155 #108.

Bit/phase repetition correct only the specified single Pauli error family.
Coherent syndrome and logical density are checked, not fault tolerance.
"""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

STATES = [(0.,0.), (np.pi,0.), (np.pi/2,np.pi/2), (.91,-.63)]
ERRORS = [None,0,1,2]


def state(theta, phi):
    return np.array([np.exp(-.5j*phi)*np.cos(theta/2),
                     np.exp(.5j*phi)*np.sin(theta/2)])


def recovery(c, theta, phi, error, phase=False):
    c.ry(theta,0); c.rz(phi,0)
    c.cx(0,1); c.cx(0,2)
    if phase:
        for i in range(3):
            c.h(i)
    if error is not None:
        (c.z if phase else c.x)(error)
    if phase:
        for i in range(3):
            c.h(i)
    c.cx(0,2); c.cx(0,1); c.ccx(1,2,0)
    return c


@pytest.mark.parametrize("phase", [False, True])
@pytest.mark.parametrize("error", ERRORS)
@pytest.mark.parametrize("theta,phi", STATES)
def test_single_pauli_recovery(phase,error,theta,phi):
    v = state(theta,phi)
    # After decoding, ancilla bits 1/2 hold error parities.
    syndrome = {None:0,0:3,1:1,2:2}[error]
    anc = np.eye(4)[syndrome]
    expected = np.kron(anc,v)
    s = recovery(q.Circuit(3),theta,phi,error,phase).run()
    n = Statevector.from_instruction(recovery(QuantumCircuit(3),theta,phi,error,phase)).data
    np.testing.assert_allclose(s.math.statevector(),expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(n,expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(s.math.density_matrix([0]),np.outer(v,v.conj()),atol=1e-9,rtol=0)


def extraction(c, theta, phi, error):
    c.ry(theta,0); c.rz(phi,0)
    c.cx(0,1); c.cx(0,2)
    if error is not None:
        c.x(error)
    c.cx(0,3); c.cx(1,3); c.cx(0,4); c.cx(2,4)
    return c


@pytest.mark.parametrize("error", ERRORS)
@pytest.mark.parametrize("theta,phi", STATES)
def test_stabilizer_syndrome_preserves_encoded_superposition(error,theta,phi):
    v = state(theta,phi)
    mask = 0 if error is None else 1 << error
    syndrome = {None:0,0:3,1:1,2:2}[error]
    expected = np.zeros(32,complex)
    expected[(syndrome<<3)|mask] = v[0]
    expected[(syndrome<<3)|(7^mask)] = v[1]
    s = extraction(q.Circuit(5),theta,phi,error).run()
    n = Statevector.from_instruction(extraction(QuantumCircuit(5),theta,phi,error)).data
    np.testing.assert_allclose(s.math.statevector(),expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(n,expected,atol=1e-9,rtol=0)


def test_double_bit_error_is_not_corrected():
    c = q.Circuit(3).cx(0,1).cx(0,2).x(1).x(2)
    c.cx(0,2).cx(0,1).ccx(1,2,0)
    # Counterexample: double error is decoded as logical |1>.
    np.testing.assert_allclose(c.run().math.density_matrix([0]),np.diag([0.,1.]),atol=1e-9,rtol=0)
