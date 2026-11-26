# ADR 001 — Native authoritative representation

Status: implemented, documented retrospectively.

Context: a high-level quantum SDK needs semantics consistent with the
existing native ecosystem and should not duplicate circuit or simulator state.

Decision: use Qiskit QuantumCircuit as the authoritative program, native
Statevector and NumPy for ideal numerical execution, and separate optional
Aer execution for dynamic shots. Replay and annotations are bounded auxiliary
data, not mutable IR.

Alternatives: own IR/compiler; generic backend-first model; multiple mutable
representations. Rejected for current scope because each introduces semantic
translation, duplication and more verification burden.

Consequences: tight native dependency is intentional; compatibility and
global phase/bit-order tests matter. Native types appear at interoperability
boundaries. No claim of backend independence or hardware portability.
