"""Application-level checks for communication and entanglement.

All reference targets are independent of candidate outputs. Small dense
numerical calculations cross-check exact admitted QContract predicates.
"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli as MP
from qcontract import Named, Pauli, Plan, Separable, ZBranch, prepare, zero_input

HALF = ((1, 0), 1)
NEG_HALF = ((-1, 0), 1)
ZERO = ((0, 0), 0)


def observe(c, plan, labels, expected):
    state = Statevector.from_instruction(c)
    numeric = tuple("PASS" if np.isclose(state.expectation_value(MP(label)),
                                          1, rtol=0, atol=1e-12) else "FAIL"
                    for label in labels)
    outcome = plan.verify(prepare(c))
    actual = tuple(r.status for _, r in outcome.results)
    assert actual == expected == numeric, (actual, expected, numeric)
    return {"expected": expected, "numeric": numeric, "reports": outcome.explain()}


def ghz_distribution():
    """Certify a three-party cat-state resource, including relative phase."""
    labels = ("XXX", "IZZ", "ZIZ")
    plan = Plan(tuple(zero_input(label, stabilizes=label) for label in labels))
    rows = []
    for case, expected in (
        ("resource", ("PASS",)*3),
        ("equivalent rewrite", ("PASS",)*3),
        ("relative phase error", ("FAIL", "PASS", "PASS")),
        ("missing receiver link", ("FAIL", "PASS", "FAIL")),
    ):
        c = QuantumCircuit(3)
        c.h(0)
        c.cx(0, 1)
        if case != "missing receiver link":
            c.cx(0, 2)
        if case == "relative phase error":
            c.z(0)
        if case == "equivalent rewrite":
            c.cx(1, 2)
            c.cx(1, 2)
        rows.append({"case": case, **observe(c, plan, labels, expected)})
    return {"cases": rows, "purpose": "certify ideal three-party GHZ resource"}


def graph_resource():
    """Verify a line cluster state using its independent stabilizers."""
    labels = ("IZX", "ZXZ", "XZI")
    plan = Plan(tuple(zero_input(label, stabilizes=label) for label in labels))
    rows = []
    for case, expected in (("line", ("PASS",)*3),
                           ("missing edge", ("PASS", "FAIL", "FAIL")),
                           ("wrong local phase", ("PASS", "FAIL", "PASS"))):
        c = QuantumCircuit(3)
        for i in range(3):
            c.h(i)
        # Express CZ in the admitted gate alphabet.
        for a,b in ((0,1), (1,2)):
            if case == "missing edge" and b == 2:
                continue
            c.h(b); c.cx(a,b); c.h(b)
        if case == "wrong local phase":
            c.z(1)
        rows.append({"case": case, **observe(c, plan, labels, expected)})
    return {"cases": rows, "purpose": "cluster resource preparation, not MBQC execution"}


def dense_coding():
    """Audit ideal coherent dense coding before readout."""
    rows = []
    for phase in (0,1):
        for bit in (0,1):
            labels = (("-" if phase else "")+"IZ", ("-" if bit else "")+"ZI")
            plan = Plan(tuple(zero_input(label, stabilizes=label) for label in labels))
            for bad in (False, True):
                c = QuantumCircuit(2)
                c.h(0); c.cx(0,1)
                if bit:
                    c.x(0)
                if phase:
                    c.z(0)
                if bad:
                    c.z(0)
                c.cx(0,1); c.h(0)
                expected = ("FAIL", "PASS") if bad else ("PASS", "PASS")
                rows.append({"message": [phase,bit], "phase_fault": bad,
                             **observe(c,plan,labels,expected)})
    return {"cases": rows, "purpose": "verify all four decoded classical messages"}


def branch_audit():
    """Certify Bell conditional correlations without dynamic execution."""
    rows = []
    for bad in (False, True):
        c = QuantumCircuit(2)
        c.h(0); c.cx(0,1)
        if bad:
            c.x(1)
        p = prepare(c)
        v = Statevector.from_instruction(c).data
        for branch in (0,1):
            expected_moment = HALF if branch == 0 else NEG_HALF
            spec = ZBranch(0, branch, Pauli("ZI"), HALF, expected_moment)
            result = p.check(spec)
            prob = sum(abs(a)**2 for i,a in enumerate(v) if i&1 == branch)
            moment = sum(abs(a)**2 * (1 if not i&2 else -1)
                         for i,a in enumerate(v) if i&1 == branch)
            numeric = "PASS" if np.allclose((prob,moment),
                         (0.5,0.5*(-1)**branch),rtol=0,atol=1e-12) else "FAIL"
            expected = "FAIL" if bad else "PASS"
            assert result.status == expected == numeric
            rows.append({"branch":branch,"receiver_fault":bad,"status":result.status,
                         "probability":float(prob),"unnormalized_z":float(moment),
                         "report":Plan((Named("Bell branch",spec),)).verify(p).explain()})
    return {"cases":rows,"purpose":"conditional receiver correlation, not feedforward"}


def partition_audit():
    """Require two independent Bell-pair resources across a fixed cut."""
    rows = []
    for coupled in (False,True):
        c = QuantumCircuit(4)
        c.h(0);c.cx(0,1);c.h(2);c.cx(2,3)
        if coupled:
            c.cx(1,2)
        p = prepare(c)
        spec = Separable(0b0011)
        plan = Plan((Named("Separate the two resources",spec),))
        outcome = plan.verify(p)
        matrix = Statevector.from_instruction(c).data.reshape(4,4)
        rank = int(np.linalg.matrix_rank(matrix,tol=1e-12))
        expected = "FAIL" if coupled else "PASS"
        assert outcome.results[0][1].status == expected == ("PASS" if rank==1 else "FAIL")
        rows.append({"cross_link":coupled,"schmidt_rank":rank,"reports":outcome.explain()})
    return {"cases":rows,"purpose":"detect unintended inter-module entanglement"}
