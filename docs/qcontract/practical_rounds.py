"""Practical author-created QContract exercises; not a public API."""
import itertools
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


def validate_secret(secret):
    if type(secret) is not tuple or len(secret) != 3 or any(
            type(bit) is not int or bit not in (0, 1) for bit in secret):
        raise ValueError("secret must contain three integer bits in wire order")
    return secret


def output_plan(secret: tuple[int, int, int]) -> Plan:
    """Zero-input output contract, independently chosen before circuit design."""
    validate_secret(secret)
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


def parity_oracle_plan(secret: tuple[int, int, int]) -> Plan:
    """All-input parity oracle: map target Z and each data X."""
    validate_secret(secret)
    parity = pauli_on(4, tuple((w, "Z") for w, bit in enumerate(secret) if bit)
                      + ((ANCILLA, "Z"),))
    target_z = pauli_on(4, ((ANCILLA, "Z"),))
    claims = [transition("Target Z parity", before=parity, after=target_z)]
    for w, bit in enumerate(secret):
        data_x = pauli_on(4, ((w, "X"),))
        support = ((w, "X"), (ANCILLA, "X")) if bit else ((w, "X"),)
        claims.append(transition(f"Data X {w}", before=pauli_on(4, support),
                                 after=data_x))
    return Plan(tuple(claims))


def oracle_circuit(edges):
    c = QuantumCircuit(4)
    for w in edges:
        c.cx(w, ANCILLA)
    return c


def modularity():
    module = parity_oracle_plan(SECRET)
    # Independently specified Pauli labels, separate from the mask authoring.
    pairs = (("ZZIZ", "ZIII"), ("XIIX", "IIIX"),
             ("IIXI", "IIXI"), ("XXII", "IXII"))
    cases = (("oracle", (0, 2), ("PASS",)*4),
             ("missing edge", (0,), ("FAIL", "PASS", "PASS", "FAIL")),
             ("extra edge", (0, 1, 2), ("FAIL", "PASS", "FAIL", "PASS")))
    rows = []
    for name, edges, expected in cases:
        c = oracle_circuit(edges)
        p = prepare(c)
        outcome = module.verify(p)
        u = Operator(c).data
        oracle = tuple("PASS" if np.allclose(
            u.conj().T @ MatrixPauli(b).to_matrix() @ u,
            MatrixPauli(a).to_matrix(), rtol=0, atol=1e-12) else "FAIL"
            for a, b in pairs)
        assert verdicts(outcome) == expected == oracle, (name, verdicts(outcome), oracle)
        rows.append({"case": name, "snapshot": p.snapshot_id,
                     "expected": expected, "reports": outcome.explain()})
    # The oracle's local correctness cannot justify the whole algorithm.
    local = module.verify(prepare(oracle_circuit((0, 2))))
    final = output_plan(SECRET).verify(prepare(bv((0, 2), cleanup=False)))
    assert local.passed and verdicts(final) == ("PASS", "PASS", "PASS", "FAIL")
    return {"module_scope": "four selected all-input observables; not full unitary",
            "cases": rows, "missing_cleanup_final": final.explain()}


def parameterized_authoring():
    """Reuse the same project-local contract factory for every 3-bit intent."""
    rows = []
    for bits in itertools.product((0, 1), repeat=3):
        plan = output_plan(bits)
        edges = tuple(w for w, bit in enumerate(bits) if bit)
        c = bv(edges)
        p = prepare(c)
        result = plan.verify(p)
        assert result.require().passed
        assert p.statuses(*(o.specification for o in plan.obligations)) == ("PASS",)*4
        probabilities = Statevector.from_instruction(c).probabilities()
        # The expected computational-basis index follows from the secret,
        # not from observing the candidate output. Ancilla is zero.
        target = sum(bit << w for w, bit in enumerate(bits))
        expected = np.zeros(16)
        expected[target] = 1
        assert np.allclose(probabilities, expected, rtol=0, atol=1e-12)
        rows.append({"secret_wire_order": bits, "basis_index": target,
                     "reports": result.explain()})
    invalid = []
    for value in ((1, 0), (1, 0, 2), (True, 0, 1), [1, 0, 1]):
        for factory in (output_plan, parity_oracle_plan):
            try:
                factory(value)
            except ValueError:
                invalid.append(factory.__name__)
            else:
                raise AssertionError("invalid project-local intent accepted")
    assert len(invalid) == 8
    return {"cases": rows, "invalid_intent_controls": len(invalid)}
