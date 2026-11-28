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


def main():
    assert sys.flags.isolated
    assert qcontract.__version__ == "0.1.0a3"
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(
        pathlib.Path(sys.prefix).resolve())
    results = {"R23_api_audit": api_audit()}
    print(json.dumps({"scope": "author-created final qualification",
                      "results": results}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
