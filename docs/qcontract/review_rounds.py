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


def composition():
    # Separate components can pass different local contracts, yet not
    # establish the intended assembled all-input transformation.
    h = circuit(1, (("h", 0),))
    z = circuit(1, (("z", 0),))
    h_plan = Plan((transition("H maps Z to X", before="Z", after="X"),
                   transition("H maps X to Z", before="X", after="Z")))
    z_plan = Plan((invariant("Z preserves Z", observable="Z"),))
    assert h_plan.verify(prepare(h)).require().passed
    assert z_plan.verify(prepare(z)).require().passed
    final = Plan((invariant("Overall Z preserved", observable="Z"),))
    pz = Pauli("Z").to_matrix()
    rows = []
    for name, gates, expected in (
        ("compatible H H", (("h", 0), ("h", 0)), "PASS"),
        ("incompatible H Z", (("h", 0), ("z", 0)), "FAIL"),
        ("compatible Z Z", (("z", 0), ("z", 0)), "PASS"),
        ("incompatible Z H", (("z", 0), ("h", 0)), "FAIL"),
    ):
        c = circuit(1, gates)
        u = Operator(c).data
        oracle = "PASS" if np.allclose(u.conj().T @ pz @ u, pz,
                                       rtol=0, atol=1e-12) else "FAIL"
        outcome = final.verify(prepare(c))
        assert statuses(outcome) == (expected,) == (oracle,)
        rows.append(dict(case=name, expected=expected, oracle=oracle,
                         observed=statuses(outcome), reports=outcome.explain()))
    return {"local_checks": 3, "rows": rows,
            "scope": "final checks, not an assume-guarantee calculus"}


def evolution():
    # Preserve the same independently declared all-input observable
    # contract across source revisions. Strict equality is separately
    # reviewed because a common global phase is allowed by the intent.
    intent = Plan((transition("H maps Z to X", before="Z", after="X"),
                   transition("H maps X to Z", before="X", after="Z")))
    reference = circuit(1, (("h", 0),))
    ref = prepare(reference)
    matrix = Operator(reference).data
    rows = []
    for name, gates, expected in (
        ("original", (("h", 0),), ("PASS", "PASS", "PASS")),
        ("HHH rewrite", (("h", 0), ("h", 0), ("h", 0)), ("PASS", "PASS", "PASS")),
        ("common negative phase", (("h", 0), ("x", 0), ("z", 0),
                                   ("x", 0), ("z", 0)), ("PASS", "PASS", "FAIL")),
        ("wrong relative phase", (("h", 0), ("z", 0)), ("FAIL", "PASS", "FAIL")),
    ):
        c = circuit(1, gates)
        p = prepare(c)
        plan = Plan(intent.obligations + (
            Named("Optional strict equality", p.equivalent_to(ref, strict=True)),))
        result = plan.verify(p)
        u = Operator(c).data
        px, pz = Pauli("X").to_matrix(), Pauli("Z").to_matrix()
        oracle = tuple("PASS" if np.allclose(a, b, rtol=0, atol=1e-12) else "FAIL"
                       for a, b in ((u.conj().T @ px @ u, pz),
                                    (u.conj().T @ pz @ u, px), (u, matrix)))
        assert statuses(result) == expected == oracle
        identities = [r.obligation for _, r in result.results[:2]]
        if rows:
            assert identities == rows[0]["intent_obligations"]
        if name != "original":
            assert result.results[0][1].snapshots != ref_outcome.results[0][1].snapshots
        else:
            ref_outcome = result
        rows.append(dict(case=name, observed=statuses(result), expected=expected,
                         oracle=oracle, intent_obligations=identities,
                         reports=result.explain()))
    # The strict check is diagnostic, not a release gate for this intent.
    assert [classify(r["observed"][:2]) for r in rows] == [
        "accepted", "accepted", "accepted", "refuted"]
    return {"rows": rows, "scope": "observable intent, common phase allowed"}


def diagnostics():
    from qcontract import pauli_on
    h = prepare(circuit(1, (("h", 0),)))
    claim = transition("H maps Z to X", before="Z", after="X")
    plan = Plan((claim,))
    unresolved = plan.verify(h, max_work=1)
    resolved = plan.verify(h)
    wrong = prepare(circuit(1, (("z", 0),)))
    failure = plan.verify(wrong)
    assert statuses(unresolved) == ("INCONCLUSIVE",)
    assert statuses(resolved) == ("PASS",)
    assert statuses(failure) == ("FAIL",)
    assert unresolved.results[0][1].obligation == resolved.results[0][1].obligation
    assert unresolved.results[0][1].snapshots == resolved.results[0][1].snapshots
    assert wrong.replay(claim.specification, failure.results[0][1]) is True
    for outcome in (unresolved, failure):
        try:
            outcome.require()
        except AssertionError:
            pass
        else:
            raise AssertionError("unresolved or refuted plan must not pass")
    try:
        pauli_on(2, ((0, "Z"), (0, "X")))
    except ValueError:
        invalid = "ValueError"
    else:
        raise AssertionError("duplicate wire must be rejected")
    # Synthetic classifier control only: this is not an engine verdict.
    assert classify(("UNSUPPORTED",)) == "unresolved"
    return {"bounded": unresolved.explain(), "resolved": resolved.explain(),
            "refuted": failure.explain(), "invalid_input": invalid,
            "unsupported_classifier_control": "synthetic; not engine evidence"}


def main():
    assert sys.flags.isolated
    assert qcontract.__version__ == "0.1.0a3"
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(
        pathlib.Path(sys.prefix).resolve())
    results = {"R1_sufficiency": sufficiency(), "R2_minimality": minimality(),
               "R3_composition": composition(), "R4_evolution": evolution(),
               "R5_diagnostics": diagnostics()}
    print(json.dumps({"scope": "author-created bounded review exercises",
                      "results": results}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
