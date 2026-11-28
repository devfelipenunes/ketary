"""Final author-controlled API audit and matched property comparisons."""
import json
import pathlib
import sys

import numpy as np
import qcontract
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli as MatrixPauli, Statevector
from qcontract import Correctable, Named, Pauli, Plan, invariant, prepare, transition, zero_input


def statuses(outcome):
    return tuple(r.status for _, r in outcome.results)


def api_audit():
    c = QuantumCircuit(1)
    c.h(0)
    p = prepare(c)
    plan = Plan((transition("Z to X", before="Z", after="X"),
                 transition("X to Z", before="X", after="Z")))
    specs = tuple(o.specification for o in plan.obligations)
    rows = []
    for budget in (1, 2, 100, 2_000_000):
        outcome = plan.verify(p, max_work=budget)
        quota = budget // len(specs)
        assert p.statuses(*specs, max_work=budget) == statuses(outcome)
        assert all(r.reserved == quota for _, r in outcome.results)
        if quota:
            assert tuple(r for _, r in outcome.results) == tuple(
                p.check(s, max_work=quota) for s in specs)
        else:
            assert statuses(outcome) == ("INCONCLUSIVE",)*2
        rows.append({"budget": budget, "quota": quota, "reports": outcome.explain()})
    # Labels are human metadata, not mathematical identity.
    renamed = Plan((Named("A different label", specs[0]), plan.obligations[1]))
    original, changed = plan.verify(p), renamed.verify(p)
    assert tuple(r for _, r in original.results) == tuple(r for _, r in changed.results)
    assert original.explain()[0]["name"] != changed.explain()[0]["name"]
    try:
        Plan((plan.obligations[0], plan.obligations[0]))
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate labels must be rejected")

    # Correctability checks a code and finite error set, not circuit gates.
    code = Correctable((Pauli("IZZ"), Pauli("ZZI")),
                       tuple(Pauli(s) for s in ("III", "IIX", "IXI", "XII")))
    a = prepare(QuantumCircuit(3))
    circuit = QuantumCircuit(3)
    circuit.h(0)
    b = prepare(circuit)
    left, right = a.check(code), b.check(code)
    assert a.snapshot_id != b.snapshot_id
    assert left.status == right.status == "PASS"
    assert left.snapshots == right.snapshots == ()
    assert left.obligation == right.obligation
    return {"budgets": rows, "duplicate_label_rejected": True,
            "circuit_independent": {"status": left.status, "snapshots": left.snapshots,
                                    "obligation": left.obligation}}


def matched_qiskit():
    # Same authored requirements and same candidate circuits on both routes.
    # The numerical baseline is a small matrix/statevector cross-check, not
    # an exact proof or a representative performance/usability experiment.
    rows = []
    for name, gates, expected in (
        ("H", ("h",), ("PASS", "PASS")),
        ("HHH", ("h", "h", "h"), ("PASS", "PASS")),
        ("HZ", ("h", "z"), ("FAIL", "PASS")),
        ("identity", (), ("FAIL", "FAIL")),
    ):
        c = QuantumCircuit(1)
        for gate in gates:
            getattr(c, gate)(0)
        pairs = (("Z", "X"), ("X", "Z"))
        plan = Plan(tuple(transition(f"{a} to {b}", before=a, after=b)
                          for a, b in pairs))
        u = Operator(c).data
        native = tuple("PASS" if np.allclose(
            u.conj().T @ MatrixPauli(b).to_matrix() @ u,
            MatrixPauli(a).to_matrix(), rtol=0, atol=1e-12) else "FAIL"
            for a, b in pairs)
        result = plan.verify(prepare(c))
        assert statuses(result) == expected == native
        rows.append({"family": "all-input observable", "case": name,
                     "expected": expected, "qiskit_numeric": native,
                     "qcontract": statuses(result), "reports": result.explain()})
    for name, suffix, expected in (
        ("Bell", (), ("PASS", "PASS")),
        ("allowed rewrite", ("h", "h"), ("PASS", "PASS")),
        ("phase error", ("z",), ("FAIL", "PASS")),
        ("bit error", ("x",), ("PASS", "FAIL")),
    ):
        c = QuantumCircuit(2)
        c.h(0)
        c.cx(0, 1)
        for gate in suffix:
            getattr(c, gate)(0)
        labels = ("XX", "ZZ")
        plan = Plan(tuple(zero_input(label, stabilizes=label) for label in labels))
        state = Statevector.from_instruction(c)
        native = tuple("PASS" if np.isclose(
            state.expectation_value(MatrixPauli(label)), 1,
            rtol=0, atol=1e-12) else "FAIL" for label in labels)
        result = plan.verify(prepare(c))
        assert statuses(result) == expected == native
        rows.append({"family": "zero-input state", "case": name,
                     "expected": expected, "qiskit_numeric": native,
                     "qcontract": statuses(result), "reports": result.explain()})
    return {"cases": rows, "matched_status_comparisons": 2*len(rows),
            "boundary": "authored small fixtures; no timings, participants or superiority claim"}


def main():
    assert sys.flags.isolated
    assert qcontract.__version__ == "0.1.0a3"
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(
        pathlib.Path(sys.prefix).resolve())
    results = {"R23_api_audit": api_audit(), "R24_matched_qiskit": matched_qiskit()}
    print(json.dumps({"scope": "author-created final qualification",
                      "results": results}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
