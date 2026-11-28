"""Finite error-model audit for two ideal repetition-code encoders.

Application example, not a hardware noise model or a fault-tolerance claim.
Run using the qualified local Alpha wheels.
"""
import json
import pathlib
import sys

import numpy as np
import qcontract
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli as MatrixPauli
from qcontract import Correctable, Named, Pauli, Plan, prepare, transition

# These requirements are fixed from code definitions, not from the encoder.
CODES = {
    "bit_repetition": {
        "stabilizers": ("IZZ", "ZIZ"),
        "logical_x": "XXX", "logical_z": "IIZ",
        "expected": ("PASS", "FAIL", "FAIL", "FAIL"),
    },
    "phase_repetition": {
        "stabilizers": ("IXX", "XIX"),
        "logical_x": "ZZZ", "logical_z": "IIX",
        "expected": ("FAIL", "PASS", "FAIL", "FAIL"),
    },
}
MODELS = {
    "single_bit_flips": ("III", "IIX", "IXI", "XII"),
    "single_phase_flips": ("III", "IIZ", "IZI", "ZII"),
    "mixed_bit_and_phase": ("III", "IIX", "IIZ"),
    "ambiguous_double_errors": ("III", "IIX", "XXI", "IIZ", "ZZI"),
}


def encoder(code_name, *, omit_edge=False):
    c = QuantumCircuit(3)
    c.cx(0, 1)
    if not omit_edge:
        c.cx(0, 2)
    if code_name == "phase_repetition":
        for wire in range(3):
            c.h(wire)
    return c


def code_basis(code_name):
    # |000>, |111> or |+++>, |--->. Independent of implementation.
    basis = np.zeros((8, 2), dtype=complex)
    basis[0, 0] = basis[7, 1] = 1
    if code_name == "phase_repetition":
        h = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        basis = np.kron(np.kron(h, h), h) @ basis
    return basis


def encoder_plan(code):
    return Plan((
        transition("First code stabilizer", before="IZI", after=code["stabilizers"][0]),
        transition("Second code stabilizer", before="ZII", after=code["stabilizers"][1]),
        transition("Logical X action", before="IIX", after=code["logical_x"]),
        transition("Logical Z action", before="IIZ", after=code["logical_z"]),
    ))


def kl_oracle(basis, labels):
    """Independent finite Knill–Laflamme matrix check over every pair."""
    matrices = [MatrixPauli(label).to_matrix() for label in labels]
    violations = []
    for i, a in enumerate(matrices):
        for j, b in enumerate(matrices):
            logical = basis.conj().T @ a.conj().T @ b @ basis
            scalar = np.trace(logical) / 2
            if not np.allclose(logical, scalar*np.eye(2), rtol=0, atol=1e-12):
                violations.append([labels[i], labels[j]])
    return ("FAIL" if violations else "PASS"), violations


def audit():
    rows = []
    encoders = []
    for name, code in CODES.items():
        basis = code_basis(name)
        candidate = encoder(name)
        plan = encoder_plan(code)
        snapshot = prepare(candidate)
        good = plan.verify(snapshot)
        assert good.require().passed
        assert np.allclose(Operator(candidate).data[:, :2], basis, rtol=0, atol=1e-12)
        wrong = plan.verify(prepare(encoder(name, omit_edge=True)))
        assert not wrong.passed and any(r.status == "FAIL" for _, r in wrong.results)
        encoders.append({"code": name, "accepted": good.explain(),
                         "missing_edge": wrong.explain()})
        for (model, errors), expected in zip(MODELS.items(), code["expected"]):
            specification = Correctable(tuple(Pauli(s) for s in code["stabilizers"]),
                                        tuple(Pauli(e) for e in errors))
            result = snapshot.check(specification)
            oracle, violations = kl_oracle(basis, errors)
            assert result.status == expected == oracle, (name, model, result.status, oracle)
            assert result.snapshots == ()  # code-only, not an encoder proof
            rows.append({"code": name, "error_model": model, "errors": errors,
                         "status": result.status, "oracle": oracle,
                         "violating_pairs": violations, "obligation": result.obligation,
                         "domain": result.domain})
    recommendations = {model: [r["code"] for r in rows
                               if r["error_model"] == model and r["status"] == "PASS"]
                       for model in MODELS}
    assert recommendations == {"single_bit_flips": ["bit_repetition"],
                               "single_phase_flips": ["phase_repetition"],
                               "mixed_bit_and_phase": [], "ambiguous_double_errors": []}
    return {"scope": "ideal finite Pauli error sets; no physical recovery claim",
            "encoders": encoders, "cases": rows, "qualified_codes_by_model": recommendations}


def main():
    assert sys.flags.isolated
    assert qcontract.__version__ == "0.1.0a3"
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(
        pathlib.Path(sys.prefix).resolve())
    print(json.dumps(audit(), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
