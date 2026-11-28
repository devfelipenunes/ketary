"""Executable checks of a trusted, bounded contract-first project example."""
import json
import pathlib
import runpy
import sys

import numpy as np
import qcontract
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli as MatrixPauli
from qcontract import Contract, Named, Pauli, Plan, pauli_on, prepare, transition

ROOT = pathlib.Path(__file__).resolve().parent
# Load only these trusted repository example files by explicit path.
# The installed qcontract wheel remains the source of the public API.
REQ = runpy.run_path(str(ROOT / "requirements.py"))
IMPL = runpy.run_path(str(ROOT / "implementation.py"))


def statuses(outcome):
    return tuple(r.status for _, r in outcome.results)


def weighted():
    plan = REQ["weighted_claim"]()
    x, z = MatrixPauli("X").to_matrix(), MatrixPauli("Z").to_matrix()
    before, after = z/3 + x/2, x/3 + z/2
    rows = []
    for gates, expected in ((("h",), "PASS"), (("h", "h", "h"), "PASS"),
                            ((), "FAIL"), (("h", "z"), "FAIL")):
        c = IMPL["weighted_example"](gates)
        p = prepare(c)
        result = plan.verify(p)
        u = Operator(c).data
        oracle = "PASS" if np.allclose(u.conj().T @ after @ u, before,
                                       rtol=0, atol=1e-12) else "FAIL"
        assert statuses(result) == (expected,) == (oracle,)
        rows.append({"gates": gates, "expected": expected,
                     "observed": statuses(result), "reports": result.explain()})
    return {"cases": rows, "scope": "all-input rational weighted observable"}


def modular():
    compute = REQ["compute_claim"]()
    phase = REQ["phase_claim"]()
    local_compute = compute.verify(prepare(IMPL["compute"]()))
    local_phase = phase.verify(prepare(IMPL["apply_phase"]()))
    inverse_phase = phase.verify(prepare(IMPL["apply_phase"](inverse=True)))
    assert local_compute.passed and local_phase.passed and inverse_phase.passed
    ref = REQ["reference"]()
    # Independent mathematical target: diag(1,exp(i*pi/4)) on logical wire 0
    # with workspace 1 clean; numerical oracle includes both input columns.
    t = np.exp(1j*np.pi/4)
    target = np.diag([1, t, 1, t])
    direct = QuantumCircuit(2)
    direct.t(0)
    fixtures = (
        ("compute phase uncompute", IMPL["phase_gadget"](), ("PASS", "PASS", "FAIL")),
        ("allowed workspace Z", IMPL["phase_gadget"](rewrite=True), ("PASS", "PASS", "FAIL")),
        ("direct logical T", direct, ("PASS", "PASS", "PASS")),
        ("missing uncompute", IMPL["phase_gadget"](cleanup=False), ("FAIL", "FAIL", "FAIL")),
        ("inverse phase", IMPL["phase_gadget"](inverse=True), ("PASS", "FAIL", "FAIL")),
    )
    rows = []
    for name, c, expected in fixtures:
        p = prepare(c)
        result = REQ["final_claim"](p, ref).verify(p)
        strict = REQ["strict_diagnostic"](p, ref).verify(p)
        u = Operator(c).data
        clean = np.allclose(u[2:, :2], 0, rtol=0, atol=1e-12)
        phase_factor = u[0, 0]
        relative = np.isclose(abs(phase_factor), 1, rtol=0, atol=1e-12) and np.allclose(
            u[:, :2], phase_factor*target[:, :2], rtol=0, atol=1e-12)
        exact = np.allclose(u, target, rtol=0, atol=1e-12)
        oracle = tuple("PASS" if v else "FAIL" for v in (clean, relative, exact))
        observed = statuses(result) + statuses(strict)
        assert observed == expected == oracle, (name, observed, expected, oracle)
        assert result.passed == all(s == "PASS" for s in expected[:2])
        rows.append({"case": name, "observed": observed, "expected": expected,
                     "required": result.explain(), "optional_strict": strict.explain()})
    return {"module_reports": [local_compute.explain(), local_phase.explain(),
                               inverse_phase.explain()], "cases": rows}


def project_gate(candidate, *, budget=2_000_000):
    # Only trusted requirements produce the Plan. The implementation
    # cannot supply its own expected specification to this entry point.
    snapshot = prepare(candidate)
    plan = REQ["final_claim"](snapshot, REQ["reference"]())
    outcome = plan.verify(snapshot, max_work=budget)
    assert all(r.snapshots and r.snapshots[0] == snapshot.snapshot_id
               for _, r in outcome.results)
    outcome.require()
    return {"snapshot_id": snapshot.snapshot_id, "budget": budget,
            "reports": outcome.explain()}


def architecture():
    accepted = project_gate(IMPL["phase_gadget"]())
    rejected = []
    for name, candidate, budget in (
        ("missing cleanup", IMPL["phase_gadget"](cleanup=False), 2_000_000),
        ("wrong logical action", IMPL["phase_gadget"](inverse=True), 2_000_000),
        ("unresolved", IMPL["phase_gadget"](), 1),
    ):
        try:
            project_gate(candidate, budget=budget)
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError("project gate accepted " + name)
    assert len(rejected) == 3
    return {"accepted": accepted, "rejected": rejected,
            "boundary": "trusted local fixture; no untrusted-code sandbox"}


def ergonomics():
    # Compare three equivalent authoring forms, not subjective UX scores.
    named = REQ["compute_claim"]().obligations[0]
    raw = Named(named.name, Contract(requires=Pauli("ZZ"), ensures=Pauli("ZI")))
    indexed = transition(named.name, before=pauli_on(2, ((0, "Z"), (1, "Z"))),
                         after=pauli_on(2, ((1, "Z"),)))
    assert named == raw == indexed
    rows = []
    for name, candidate, expected in (
        ("compute", IMPL["compute"](), "PASS"),
        ("identity", QuantumCircuit(2), "FAIL"),
    ):
        snapshot = prepare(candidate)
        for budget in (1, 2_000_000):
            outcomes = [Plan((claim,)).verify(snapshot, max_work=budget)
                        for claim in (named, raw, indexed)]
            want = "INCONCLUSIVE" if budget == 1 else expected
            assert all(statuses(o) == (want,) for o in outcomes)
            assert outcomes[0].explain() == outcomes[1].explain() == outcomes[2].explain()
            rows.append({"case": name, "budget": budget, "reports": outcomes[0].explain()})
    return {"comparisons": rows,
            "decision": "Use the simplest readable syntax; no productivity claim."}


def main():
    assert sys.flags.isolated
    assert qcontract.__version__ == "0.1.0a3"
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(
        pathlib.Path(sys.prefix).resolve())
    results = {"R16_expressivity": weighted(), "R17_modules": modular(),
               "R18_architecture": architecture(), "R19_ergonomics": ergonomics()}
    print(json.dumps({"scope": "bounded practical project example",
                      "results": results}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
