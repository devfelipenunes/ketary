# Candidate ADR — Public native instruction field access

The #478 research head measured public CircuitInstruction fields and native
counting on identical ordered outputs. Promote only read-only logical
inspection, resource arity and replay record construction to direct fields.
No private Qiskit interface, new IR, changed admission or global cache.
Inspection still indexes only the selected window; no full scan or index
map is added there. Replay constructs a call-local qubit index map only
after the existing complete native whitelist validation. Resource arities
use the actual attached wires, while count_ops and depth stay native.
Maintain exact JSON schema, ordering, phase, report and error semantics.
Benchmark complete reports against old routes and require exact-head CI.
This is a concrete responsibility refinement, not a module split by size.
