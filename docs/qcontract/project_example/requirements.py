"""Independent, reviewed mathematical requirements for a small example project."""
from fractions import Fraction

from qiskit import QuantumCircuit
from qcontract import Named, Pauli, Plan, SumTransition, clean_ancillas, invariant, prepare, transition


def weighted_claim():
    return Plan((Named("Transform rational observable",
                       SumTransition(((Pauli("Z"), Fraction(1, 3)),
                                      (Pauli("X"), Fraction(1, 2))),
                                     ((Pauli("X"), Fraction(1, 3)),
                                      (Pauli("Z"), Fraction(1, 2))))),))


def compute_claim():
    return Plan((transition("Copy logical Z to workspace parity", before="ZZ", after="ZI"),
                 invariant("Preserve logical Z", observable="IZ")))


def phase_claim():
    return Plan((invariant("Preserve workspace Z", observable="ZI"),
                 invariant("Preserve logical Z", observable="IZ")))


def reference():
    c = QuantumCircuit(2)
    c.t(0)
    return prepare(c)


def final_claim(snapshot, ref):
    # Scope: all logical inputs with workspace 1 initially clean;
    # common phase allowed. Cleanup is an explicit diagnostic implied by
    # matching this reference on the clean-input subspace.
    return Plan((clean_ancillas("Workspace clean", wires=(1,)),
                 Named("Logical T on clean workspace", snapshot.action_matches(ref, ancillas=(1,)))))


def strict_diagnostic(snapshot, ref):
    return Plan((Named("Full-register strict equality", snapshot.equivalent_to(ref, strict=True)),))
