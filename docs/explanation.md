# Explanation: why Ketary is an abstraction, not a simulator

QuantumCircuit is authoritative. Construction calls native gates;
statevector execution delegates to Qiskit. Ketary adds reusable snapshots,
mathematical inspection, checks, explicit diagnostics and resource guards.

For a pure state, the Born rule gives |amplitude| squared. Fidelity is
the squared overlap divided by the product of squared norms. Equal
computational-basis distributions can hide relative phase. Complete
operator comparison is stronger than a zero-input state comparison.
Global phase is ignored only when explicitly appropriate; a controlled
operation can turn it into an observable relative phase.

A dense statevector scales exponentially with qubits, and a dense
operator scales as 4**n. Trace adds a snapshot per gate. Payload limits
are not whole-process guarantees. Entropy uses SVD and can be expensive;
text drawings and dictionaries also allocate memory. Use small examples,
explicit limits and targeted queries.

Logical gate cancellation is conservative, not device-aware optimization.
Hardware execution and noise remain outside scope. Symbolic binding and restricted mid-circuit measurement/control via optional Aer were added after the original L0 spike. Logical transpilation is bounded and not device-aware. See [architecture](architecture.md) for current modes and boundaries.
