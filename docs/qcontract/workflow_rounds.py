"""Bounded developer-workflow exercises; no public API or external study."""
import json
import pathlib
import sys

import numpy as np
import qcontract
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli as MatrixPauli
from qcontract import Named, Pauli, Plan, invariant, pauli_on, prepare, transition


def verdicts(outcome):
    return tuple(r.status for _, r in outcome.results)


def authoring():
    # Intent: implement CNOT action on a complete Pauli generator set.
    # Fix the expected action and wire roles before creating any circuit.
    pairs = (("IX", "XX"), ("ZI", "ZZ"), ("IZ", "IZ"), ("XI", "XI"))
    plan = Plan(tuple(transition(f"Map {a} to {b}", before=a, after=b)
                      for a, b in pairs))
    cases = (("intended", ((0, 1),), ("PASS",)*4),
             ("equivalent triple", ((0, 1),)*3, ("PASS",)*4),
             ("missing entangler", (), ("FAIL", "FAIL", "PASS", "PASS")),
             ("reversed wires", ((1, 0),), ("FAIL",)*4))
    rows = []
    for name, edges, expected in cases:
        c = QuantumCircuit(2)
        for control, target in edges:
            c.cx(control, target)
        p = prepare(c)
        outcome = plan.verify(p)
        u = Operator(c).data
        oracle = tuple("PASS" if np.allclose(
            u.conj().T @ MatrixPauli(b).to_matrix() @ u,
            MatrixPauli(a).to_matrix(), rtol=0, atol=1e-12) else "FAIL"
            for a, b in pairs)
        assert verdicts(outcome) == expected == oracle, (name, verdicts(outcome), oracle)
        rows.append({"case": name, "expected": expected, "observed": verdicts(outcome),
                     "reports": outcome.explain()})
    return {"intent": "CNOT generator action, common phase permitted",
            "wire_roles": {"control": 0, "target": 1}, "cases": rows}
