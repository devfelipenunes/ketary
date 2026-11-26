"""Bounded generated algebra with independent dense oracle and deletion shrink.

Refs #311 #90 #136. Seeds and minimal-with-respect-to-single-deletion
counterexamples are reported for each algebra assertion. Runtime exceptions
propagate unchanged; reduction does not minimize continuous angles. This is not exhaustive verification.
"""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1., -1.])
I = np.eye(2)
H = (X + Z) / np.sqrt(2)
ATOL = 1e-9


def generated(seed, n):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(12):
        gate = str(rng.choice(["h", "rx", "ry", "rz", "cx"]))
        a, b = map(int, rng.choice(n, size=2, replace=False))
        angle = float(rng.uniform(-np.pi, np.pi))
        rows.append((gate, a, b, angle))
    v = rng.normal(size=2**n) + 1j*rng.normal(size=2**n)
    w = rng.normal(size=2**n) + 1j*rng.normal(size=2**n)
    return rows, v/np.linalg.norm(v), w/np.linalg.norm(w)


def dense(n, rows):
    total = np.eye(2**n, dtype=complex)
    for gate, a, b, angle in rows:
        if gate == "cx":
            step = np.zeros_like(total)
            for j in range(2**n):
                step[j ^ (((j >> a) & 1) << b), j] = 1
        else:
            g = H if gate == "h" else (
                np.cos(angle/2)*I - 1j*np.sin(angle/2)*{"rx": X, "ry": Y, "rz": Z}[gate])
            step = np.array([[1]], dtype=complex)
            for k in reversed(range(n)):
                step = np.kron(step, g if k == a else I)
        total = step @ total
    return total


def build(n, rows, native=False):
    c = QuantumCircuit(n) if native else q.Circuit(n)
    for gate, a, b, angle in rows:
        if gate == "cx":
            c.cx(a, b)
        elif gate == "h":
            c.h(a)
        else:
            getattr(c, gate)(angle, a)
    return c


def shrink(rows, fails):
    """Deterministic deletion-only reducer; preserves the failing predicate."""
    current = list(rows)
    if not fails(current):
        raise ValueError("input must reproduce the failure")
    while True:
        for k in range(len(current)):
            candidate = current[:k] + current[k+1:]
            if fails(candidate):
                current = candidate
                break
        else:
            return current


def defect(n, rows):
    actual = Operator(build(n, rows).to_qiskit()).data
    return not np.allclose(actual, dense(n, rows), atol=ATOL, rtol=0)


def assert_algebra(n, rows, v, w):
    assert not defect(n, rows), "full operator differs"
    u = dense(n, rows)
    c = build(n, rows)
    before = c.to_qiskit()
    np.testing.assert_allclose(Operator(build(n, rows, native=True)).data, u, atol=ATOL, rtol=0)
    np.testing.assert_allclose(u.conj().T @ u, np.eye(2**n), atol=ATOL, rtol=0)
    combined = build(n, rows[:len(rows)//2]).compose(build(n, rows[len(rows)//2:]))
    np.testing.assert_allclose(Operator(combined.to_qiskit()).data, u, atol=ATOL, rtol=0)
    first = c.run(initial_state=v)
    saved = first.math.statevector()
    for state in (v, w):
        result = c.run(initial_state=state)
        expected = u @ state
        got = result.math.statevector()
        np.testing.assert_allclose(got, expected, atol=ATOL, rtol=0)
        np.testing.assert_allclose(np.linalg.norm(got), 1., atol=ATOL, rtol=0)
        np.testing.assert_allclose(c.inverse().run(initial_state=got).math.statevector(), state, atol=ATOL, rtol=0)
        x = np.kron(np.eye(2**(n-1)), X)
        z = np.kron(np.eye(2**(n-1)), Z)
        want = np.vdot(expected, (0.7*x - 0.4*z) @ expected).real
        np.testing.assert_allclose(result.math.expectation(0.7*q.X(0)-0.4*q.Z(0)), want, atol=ATOL, rtol=0)
        np.testing.assert_allclose(result.math.expectation(0.7*q.X(0)-0.4*q.Z(0)),
                                   0.7*result.math.expectation(q.X(0))-0.4*result.math.expectation(q.Z(0)),
                                   atol=ATOL, rtol=0)
    np.testing.assert_array_equal(first.math.statevector(), saved)
    assert c.to_qiskit() == before


def failure_site(n, rows, v, w):
    """Return the specific algebra assertion that failed, not another defect."""
    try:
        assert_algebra(n, rows, v, w)
    except AssertionError as error:
        tb = error.__traceback__
        while tb is not None:
            if tb.tb_frame.f_code is assert_algebra.__code__:
                return tb.tb_lineno
            tb = tb.tb_next
        raise
    return None


@pytest.mark.parametrize("n", [2, 3])
@pytest.mark.parametrize("seed", range(31101, 31117))
def test_generated_unitary_algebra(n, seed):
    rows, v, w = generated(seed, n)
    site = failure_site(n, rows, v, w)
    if site is not None:
        reduced = shrink(rows, lambda r: failure_site(n, r, v, w) == site)
        assert failure_site(n, reduced, v, w) == site
        pytest.fail(f"seed={seed}, width={n}, assertion_line={site}, reduced={reduced!r}")

def test_shrinker_retains_real_operator_defect():
    rows = [("h", 0, 1, 0.), ("cx", 0, 1, 0.), ("rz", 1, 0, .31)]
    def fails(items):
        mutated = [("cx", b, a, t) if gate == "cx" else (gate, a, b, t)
                   for gate, a, b, t in items]
        return not np.allclose(dense(2, items), dense(2, mutated), atol=ATOL, rtol=0)
    reduced = shrink(rows, fails)
    assert reduced == [rows[1]]
    assert fails(reduced)
    assert not fails([])
    with pytest.raises(ValueError):
        shrink([], fails)


def test_shrinking_keeps_the_same_assertion(monkeypatch):
    rows, v, w = generated(31101, 2)
    def injected(n, items, v, w):
        assert len(items) > 0, "unrelated empty-circuit failure"
        assert not any(row[0] == "cx" for row in items), "target defect"
    monkeypatch.setitem(globals(), "assert_algebra", injected)
    site = failure_site(2, rows, v, w)
    assert site is not None
    reduced = shrink(rows, lambda r: failure_site(2, r, v, w) == site)
    assert len(reduced) == 1 and reduced[0][0] == "cx"
    assert failure_site(2, [], v, w) != site
