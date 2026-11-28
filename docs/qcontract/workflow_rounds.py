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


def ergonomics():
    c = QuantumCircuit(1)
    c.s(0)
    p = prepare(c)
    # S dagger X S = -Y; S dagger Y S = X.
    x = pauli_on(1, ((0, "X"),))
    y = pauli_on(1, ((0, "Y"),))
    minus_y = pauli_on(1, ((0, "Y"),), negative=True)
    assert x == Pauli("X") and y == Pauli("Y") and minus_y == Pauli("-Y")
    text = Plan((transition("Signed X image", before="-Y", after="X"),
                 transition("Y image", before="X", after="Y")))
    indexed = Plan((transition("Signed X image", before=minus_y, after=x),
                    transition("Y image", before=x, after=y)))
    rows = []
    for budget in (1, 2_000_000):
        a = text.verify(p, max_work=budget)
        b = indexed.verify(p, max_work=budget)
        expected = ("INCONCLUSIVE",)*2 if budget == 1 else ("PASS",)*2
        assert verdicts(a) == verdicts(b) == expected
        assert a.explain() == b.explain()
        specs = tuple(o.specification for o in indexed.obligations)
        assert p.statuses(*specs, max_work=budget) == expected
        rows.append({"budget": budget, "reports": a.explain(), "statuses": expected})
    # A mask does not retain the width of its authoring expression.
    too_wide = invariant("Outside prepared width", observable=pauli_on(2, ((1, "Z"),)))
    try:
        Plan((too_wide,)).verify(p)
    except ValueError:
        invalid = "ValueError"
    else:
        raise AssertionError("out-of-width mask must be rejected")
    return {"rows": rows, "invalid_width": invalid}


def admission():
    # A valid specification can exceed an implemented domain without
    # being mathematically false. Six wires exceed strict equality's
    # limit but not common-phase equality's limit.
    c = QuantumCircuit(6)
    c.h(0)
    p = prepare(c)
    plan = Plan((Named("Common-phase equality", p.equivalent_to(p)),
                 Named("Strict equality", p.equivalent_to(p, strict=True)),
                 invariant("Z on untouched wire", observable=pauli_on(6, ((5, "Z"),))),
                 invariant("X on H wire", observable=pauli_on(6, ((0, "X"),)))))
    outcome = plan.verify(p)
    expected = ("PASS", "UNSUPPORTED", "PASS", "FAIL")
    assert verdicts(outcome) == expected, verdicts(outcome)
    specs = tuple(o.specification for o in plan.obligations)
    assert p.statuses(*specs) == expected
    assert not outcome.passed
    try:
        outcome.require()
    except AssertionError:
        pass
    else:
        raise AssertionError("mixed verdict must not open execution gate")
    return {"expected": expected, "observed": verdicts(outcome),
            "reports": outcome.explain()}
