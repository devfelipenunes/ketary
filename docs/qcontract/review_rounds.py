"""Author-controlled methodology exercises; not SDK runtime or user-study data."""
import json
import pathlib
import sys

import numpy as np
import qcontract
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli, Statevector
from qcontract import Named, Plan, invariant, prepare, transition, zero_input

STATUSES = {"PASS", "FAIL", "INCONCLUSIVE", "UNSUPPORTED"}


def classify(statuses):
    """Conjunctive verdict for review, not a new proof status."""
    if not statuses or any(s not in STATUSES for s in statuses):
        raise ValueError("nonempty vector of valid statuses required")
    if "FAIL" in statuses:
        return "refuted"
    if all(s == "PASS" for s in statuses):
        return "accepted"
    return "unresolved"


def summarize(rows):
    counts = {kind: {v: 0 for v in ("accepted", "refuted", "unresolved")}
              for kind in ("positive", "defect", "allowed")}
    for row in rows:
        counts[row["kind"]][classify(row["observed"])] += 1
    return counts


def statuses(outcome):
    return tuple(r.status for _, r in outcome.results)


def circuit(width, gates):
    c = QuantumCircuit(width)
    for gate, *wires in gates:
        getattr(c, gate)(*wires)
    return c


def bell(suffix=()):
    return circuit(2, (("h", 0), ("cx", 0, 1)) + suffix)


def sufficiency():
    labels = ("XX", "ZZ")
    plan = Plan(tuple(zero_input(label, stabilizes=label) for label in labels))
    fixtures = (
        ("bell", (), "positive", ("PASS", "PASS")),
        ("phase flip", (("z", 0),), "defect", ("FAIL", "PASS")),
        ("bit flip", (("x", 0),), "defect", ("PASS", "FAIL")),
        ("both", (("x", 0), ("z", 0)), "defect", ("FAIL", "FAIL")),
        ("identity rewrite", (("h", 1), ("h", 1)), "allowed", ("PASS", "PASS")),
        ("paired phase", (("z", 0), ("z", 1)), "allowed", ("PASS", "PASS")),
    )
    rows = []
    for name, suffix, kind, expected in fixtures:
        c = bell(suffix)
        outcome = plan.verify(prepare(c))
        observed = statuses(outcome)
        v = Statevector.from_instruction(c)
        oracle = tuple("PASS" if np.isclose(v.expectation_value(Pauli(p)), 1,
                                             rtol=0, atol=1e-12) else "FAIL"
                       for p in labels)
        assert observed == expected == oracle, (name, observed, expected, oracle)
        rows.append(dict(case=name, kind=kind, expected=expected, observed=observed,
                         oracle=oracle, reports=outcome.explain()))
    counts = summarize(rows)
    assert counts == {"positive": {"accepted": 1, "refuted": 0, "unresolved": 0},
                      "defect": {"accepted": 0, "refuted": 3, "unresolved": 0},
                      "allowed": {"accepted": 2, "refuted": 0, "unresolved": 0}}
    # A refuted conjunction may also have an unresolved obligation.
    assert classify(("FAIL", "INCONCLUSIVE")) == "refuted"
    assert classify(("PASS", "UNSUPPORTED")) == "unresolved"
    return {"rows": rows, "counts": counts}


def minimality():
    x = zero_input("X correlation", stabilizes="XX")
    z = zero_input("Z correlation", stabilizes="ZZ")
    # X and Z are necessary against these controls. An exact duplicate
    # with a different human-readable name is only diagnostic metadata.
    duplicate = zero_input("Second label for X", stabilizes="XX")
    cases = (("phase", bell((("z", 0),))),
             ("bit", bell((("x", 0),))),
             ("both", bell((("x", 0), ("z", 0)))))
    rows = []
    for name, c in cases:
        p = prepare(c)
        original = Plan((x, z)).verify(p)
        extended = Plan((x, z, duplicate)).verify(p)
        assert statuses(extended) == statuses(original) + statuses(original)[:1]
        assert extended.results[0][1].obligation == extended.results[2][1].obligation
        a = Plan((x,)).verify(p)
        b = Plan((z,)).verify(p)
        assert statuses(a) == statuses(original)[:1]
        assert statuses(b) == statuses(original)[1:]
        rows.append({"case": name, "both": statuses(original),
                     "x_only": statuses(a), "z_only": statuses(b),
                     "duplicate": statuses(extended)})
    counts = {key: sum("FAIL" in r[key] for r in rows)
              for key in ("both", "x_only", "z_only", "duplicate")}
    assert counts == {"both": 3, "x_only": 2, "z_only": 2, "duplicate": 3}
    return {"rows": rows, "detected": counts,
            "scope": "three seeded defects; not general minimality"}
