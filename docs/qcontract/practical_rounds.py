"""Practical author-created QContract exercises; not a public API."""
import json
import pathlib
import sys

import numpy as np
import qcontract
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli as MatrixPauli, Statevector
from qcontract import Named, Pauli, Plan, invariant, pauli_on, prepare, transition, zero_input


SECRET = (1, 0, 1)
ANCILLA = 3


def verdicts(outcome):
    return tuple(r.status for _, r in outcome.results)


def output_plan(secret):
    """Zero-input output contract, independently chosen before circuit design."""
    return Plan(tuple(zero_input(f"Output bit {wire}",
                                 stabilizes=pauli_on(4, ((wire, "Z"),),
                                                     negative=bool(bit)))
                      for wire, bit in enumerate(secret)) +
                (zero_input("Ancilla returned to zero", stabilizes="ZIII"),))


def bv(edges, *, cleanup=True, rewrite=False):
    """Coherent Bernstein–Vazirani example without measurement."""
    c = QuantumCircuit(4)
    c.x(ANCILLA)
    for wire in range(4):
        c.h(wire)
    for wire in edges:
        c.cx(wire, ANCILLA)
        if rewrite:
            c.cx(wire, ANCILLA)
            c.cx(wire, ANCILLA)
    for wire in range(3):
        c.h(wire)
    if cleanup:
        c.h(ANCILLA)
        c.x(ANCILLA)
    return c


def algorithm():
    plan = output_plan(SECRET)
    # Qiskit labels are high-wire first; target bit string is 0101.
    labels = ("-IIIZ", "IIZI", "-IZII", "ZIII")
    assert tuple(o.specification.observable for o in plan.obligations) == tuple(
        Pauli(label) for label in labels)
    cases = (("original", bv((0, 2)), ("PASS",)*4),
             ("triple-CNOT rewrite", bv((0, 2), rewrite=True), ("PASS",)*4),
             ("missing edge", bv((0,)), ("PASS", "PASS", "FAIL", "PASS")),
             ("extra edge", bv((0, 1, 2)), ("PASS", "FAIL", "PASS", "PASS")),
             ("missing cleanup", bv((0, 2), cleanup=False),
              ("PASS", "PASS", "PASS", "FAIL")))
    rows = []
    for name, c, expected in cases:
        state = Statevector.from_instruction(c)
        oracle = tuple("PASS" if np.isclose(state.expectation_value(MatrixPauli(label)),
                                             1, rtol=0, atol=1e-12) else "FAIL"
                       for label in labels)
        result = plan.verify(prepare(c))
        assert verdicts(result) == expected == oracle, (name, verdicts(result), oracle)
        rows.append({"case": name, "expected": expected, "observed": verdicts(result),
                     "oracle": oracle, "reports": result.explain()})
    return {"scope": "ideal zero-input coherent BV; no hardware or query advantage claim",
            "cases": rows}
