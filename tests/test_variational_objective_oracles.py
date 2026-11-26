"""Independent bounded variational objective histories, refs #293 #181.

Fixed grid optimizer for reproducibility, not a chemistry or speed claim.
The two-qubit toy Hamiltonian has no asserted molecular provenance.
"""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp

I = np.eye(2)
X = np.array([[0,1],[1,0]], complex)
Y = np.array([[0,-1j],[1j,0]], complex)
Z = np.diag([1.,-1.])
PAULIS = {"I": I, "X": X, "Y": Y, "Z": Z}
GRID = np.linspace(-np.pi, np.pi, 65)
CASES = {
    "toy_h2": (2, {"II": -.2, "ZZ": -.8, "XX": .45, "ZI": .2}),
    "noncommuting_spin": (1, {"X": .8, "Z": -.4}),
    # H=Z, penalize ground |1> with 3|1><1|.
    "excited_penalty": (1, {"I": 1.5, "Z": -.5}),
    "multi_observable": (1, {"X": .7, "Z": -.4, "I": .2}),
}


def sdk(theta, n, phi=0.):
    c = q.Circuit(n).ry(theta, 0)
    if phi:
        c.rz(phi, 0)
    if n == 2:
        c.cx(0, 1)
    return c


def native(theta, n, phi=0.):
    c = QuantumCircuit(n)
    c.ry(theta, 0)
    if phi:
        c.rz(phi, 0)
    if n == 2:
        c.cx(0, 1)
    return c


def analytic(theta, n, phi=0.):
    v = np.array([np.exp(-.5j*phi)*np.cos(theta/2),
                  np.exp(.5j*phi)*np.sin(theta/2)])
    if n == 2:
        return np.array([v[0], 0., 0., v[1]])
    return v


def matrix(terms):
    out = 0
    for label, coeff in terms.items():
        term = np.array([[1.]])
        for letter in label:
            term = np.kron(term, PAULIS[letter])
        out = out + coeff*term
    return out


@pytest.mark.parametrize("name", list(CASES))
def test_variational_optimization_history(name):
    n, terms = CASES[name]
    H = matrix(terms)
    op = SparsePauliOp.from_list(list(terms.items()))
    expected = []
    got = []
    raw = []
    for angle in GRID:
        t = float(angle)
        v = analytic(t, n)
        result = sdk(t,n).run()
        baseline = Statevector.from_instruction(native(t,n))
        np.testing.assert_allclose(result.math.statevector(), v, atol=1e-9, rtol=0)
        np.testing.assert_allclose(baseline.data, v, atol=1e-9, rtol=0)
        expected.append(float(np.vdot(v, H @ v).real))
        got.append(sum(coef*result.math.expectation(label) for label,coef in terms.items()))
        raw.append(float(baseline.expectation_value(op).real))
    np.testing.assert_allclose(got, expected, atol=1e-9, rtol=0)
    np.testing.assert_allclose(raw, expected, atol=1e-9, rtol=0)
    # Independently diagonalize; finite-grid resolution is explicit.
    exact = float(np.linalg.eigvalsh(H)[0])
    assert exact - 1e-9 <= min(got) <= exact + .005
    assert exact - 1e-9 <= min(raw) <= exact + .005
    if name == "excited_penalty":
        t = float(GRID[int(np.argmin(got))])
        assert abs(sdk(t,n).run().math.expectation("Z")-1.) < 1e-9


def test_variational_complex_state_overlap():
    theta, phi = .73, .8
    target = analytic(theta,1,phi)
    expected = np.cos((GRID-theta)/2)**2
    scores = []
    raw = []
    for angle in GRID:
        t = float(angle)
        v = sdk(t,1,phi).run().math.statevector()
        w = Statevector.from_instruction(native(t,1,phi)).data
        scores.append(abs(np.vdot(target,v))**2)
        raw.append(abs(np.vdot(target,w))**2)
    np.testing.assert_allclose(scores, expected, atol=1e-9, rtol=0)
    np.testing.assert_allclose(raw, expected, atol=1e-9, rtol=0)
    assert max(scores) > .999
