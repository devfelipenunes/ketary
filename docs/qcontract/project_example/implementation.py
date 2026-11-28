"""Candidate implementations; never derive the expected contract here."""
from qiskit import QuantumCircuit


def compute():
    c = QuantumCircuit(2)
    c.cx(0, 1)
    return c


def apply_phase(*, inverse=False):
    c = QuantumCircuit(2)
    if inverse:
        c.tdg(1)
    else:
        c.t(1)
    return c


def phase_gadget(*, cleanup=True, inverse=False, rewrite=False):
    c = QuantumCircuit(2)
    c.compose(compute(), inplace=True)
    c.compose(apply_phase(inverse=inverse), inplace=True)
    if cleanup:
        c.compose(compute(), inplace=True)
    if rewrite:
        c.z(1)
    return c


def weighted_example(gates):
    c = QuantumCircuit(1)
    for gate in gates:
        getattr(c, gate)(0)
    return c
