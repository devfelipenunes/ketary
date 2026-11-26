# Alpha parallel performance research

Status: research-only candidate. No installed SDK changes. Reuse existing
issues #52, #90, #100, #190, #303, #310 and #352. Do not duplicate issues.

## Native boundary

Qiskit documents CircuitInstruction as a Rust-backed handle. Public fields
name, params and qubits can be read without asking for an operation object.
QuantumCircuit.count_ops supplies native counts. Measure equal ordered
records and count dictionaries with a one-time qubit index map versus
per-operation lookup. Preserve exact order and values. The profile is
inspection only, not an admission validator or simulation benchmark.
See IBM circuit API and CircuitInstruction documentation:
https://quantum.cloud.ibm.com/docs/en/api/qiskit/circuit
https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.CircuitInstruction
Qiskit upstream notes that _accelerate is internal:
https://github.com/orgs/Qiskit/discussions/41
Do not import private acceleration APIs in installed code.

## Architecture and mathematics

Extend the existing architecture_inventory with exact source locations of
copy, allocation, native materialization, linear algebra, serialization
and validation syntax sites in every runtime module. Static syntax is
not dynamic execution frequency or an allocation count. Prioritize only
with runtime measurements. No new architecture layer.

The commutation lab compares deterministic first-fit group construction
by direct label scan and binary symplectic masks, with exact group equality.
General commutation and qubit-wise commutation are distinct. No optimal
coloring, simultaneous hardware measurement or quantum advantage claim.

## CI and benchmark plan

One research branch instead of several competing full SDK runs. Smoke
tests validate both experiments in the existing test suite. Full artifact
collects widths 4/8/12/20 and 10/50/100/500/1000 logical instructions for
inspection (not execution), plus 64–256 Pauli terms. Three seeds, nine
randomized repetitions, raw timings and p50/p95. Preserve all negative
results. Review current full workflow and cancellation policy before
changing it; never skip exact-head mandatory gates. Dedicated host and
isolated RSS are separate qualification tasks. No CI reduction assumed.

Next: compare exact phase, ownership, full program and end-to-end
Ketary/Qiskit workloads, then select only measured candidates. The
existing rewrite ladder and application atlas remain the basis for
expressivity; do not add synonyms or count variants as new applications.
