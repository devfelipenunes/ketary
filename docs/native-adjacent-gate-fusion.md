# Adjacent native gate fusion

Issue #304. Research-only ablation of adjacent same-axis native single
and two-wire Pauli rotations and exact involutions. No reordering or
new IR; a native QuantumCircuit is authoritative. Numeric sums bounded
to moderate angle magnitude, no modulo 2pi reduction; symbolic native
identities preserved, global phase explicit. Unsupported instructions
reject. This prototype is restricted to known plain research fixtures,
not a general optimizer or verified native import path.

Twelve workloads (3/6/8 wires, 8/64 layers, numeric/symbolic), explicit
bindings, nonzero complex input, strict full operator equality including
phase; compare original/fused execution both before and after common
u/cx basis lowering at level 0. Raw fusion preparation and execution
timings separate, p50/p95, instruction counts and retained state bytes.
No process RSS or universal speed claim; constructed workload deliberately
contains fusion opportunities. Twelve regression cases including negative
controls, distinct wires, symbolic identity and phase. No runtime change.
