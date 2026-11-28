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


def traceability():
    # Keep a frozen mathematical claim and prepare a new snapshot after
    # modifying the mutable circuit object.
    c = QuantumCircuit(1)
    c.h(0)
    plan = Plan((transition("H maps Z to X", before="Z", after="X"),))
    old = prepare(c)
    first = plan.verify(old)
    c.x(0)
    c.z(0)
    current = prepare(c)
    stale = plan.verify(old)
    revised = plan.verify(current)
    assert verdicts(first) == verdicts(stale) == ("PASS",)
    assert verdicts(revised) == ("FAIL",)
    assert old.snapshot_id != current.snapshot_id
    assert first.explain() == stale.explain()
    a, b = first.results[0][1], revised.results[0][1]
    assert a.obligation == b.obligation
    assert a.snapshots != b.snapshots
    assert current.replay(plan.obligations[0].specification, b) is True
    return {"original": first.explain(), "stale": stale.explain(),
            "revised": revised.explain(),
            "rule": "Only reports bound to the intended snapshot qualify."}


def verify_release_gate(snapshot, plan, reviewed_plan, *, budget):
    """Project-local example: verify afresh; never trust a saved PASS."""
    required_names = tuple(o.name for o in reviewed_plan.obligations)
    if plan.obligations != reviewed_plan.obligations:
        raise ValueError("plan differs from reviewed specification and labels")
    outcome = plan.verify(snapshot, max_work=budget)
    if tuple(name for name, _ in outcome.results) != required_names:
        raise AssertionError("result manifest mismatch")
    if any(not r.snapshots or r.snapshots[0] != snapshot.snapshot_id
           for _, r in outcome.results):
        raise AssertionError("result snapshot mismatch")
    outcome.require()
    return {"snapshot_id": snapshot.snapshot_id, "required_names": required_names,
            "requested_work": budget, "reports": outcome.explain()}


def evidence_gate():
    c = QuantumCircuit(1)
    c.h(0)
    p = prepare(c)
    plan = Plan((transition("Z to X", before="Z", after="X"),
                 transition("X to Z", before="X", after="Z")))
    reviewed = Plan((transition("Z to X", before="Z", after="X"),
                     transition("X to Z", before="X", after="Z")))
    evidence = verify_release_gate(p, plan, reviewed, budget=2_000_000)
    assert all(row["status"] == "PASS" for row in evidence["reports"])
    reduced = Plan(plan.obligations[:1])
    blocked = []
    try:
        verify_release_gate(p, reduced, reviewed, budget=2_000_000)
    except ValueError:
        blocked.append("missing obligation")
    changed = Plan((transition("Z to X", before="Z", after="Z"),
                    plan.obligations[1]))
    try:
        verify_release_gate(p, changed, reviewed, budget=2_000_000)
    except ValueError:
        blocked.append("same name changed specification")
    try:
        verify_release_gate(p, plan, reviewed, budget=1)
    except AssertionError:
        blocked.append("unresolved")
    c.z(0)
    try:
        verify_release_gate(prepare(c), plan, reviewed, budget=2_000_000)
    except AssertionError:
        blocked.append("refutation after edit")
    assert blocked == ["missing obligation", "same name changed specification", "unresolved", "refutation after edit"]
    return {"accepted": evidence, "blocked": blocked,
            "boundary": "Example checks frozen specifications and labels, not signed provenance; "
                        "source revision and specification review remain external."}


def main():
    assert sys.flags.isolated
    assert qcontract.__version__ == "0.1.0a3"
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(
        pathlib.Path(sys.prefix).resolve())
    results = {"R6_authoring": authoring(), "R7_ergonomics": ergonomics(),
               "R8_admission": admission(), "R9_traceability": traceability(),
               "R10_evidence_gate": evidence_gate()}
    print(json.dumps({"scope": "author-created developer-workflow exercises",
                      "results": results}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
