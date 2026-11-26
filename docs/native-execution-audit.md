# Native execution engine audit — PERF02

## Motivation

Ketary owns high-level validation and immutable snapshots; Qiskit
QuantumCircuit is the authoritative model. The existing ideal execution
delegates to Qiskit quantum_info.Statevector, which uses NumPy matrix
contractions. Qiskit Aer has a specialized compiled simulator with CPU
threading, gate fusion and optional GPU/MPI. QuEST v4 has a C++17 backend,
native specialized operations and CPU/OpenMP, GPU and distributed paths.
Do not equate Qiskit Statevector with Aer.

References: [Statevector source](https://github.com/Qiskit/qiskit/blob/2.6.2/qiskit/quantum_info/states/statevector.py),
[Aer options](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html),
[QuEST source](https://github.com/QuEST-Kit/QuEST/tree/9d7618d7263e3bfba433b88cf1eac0647f08fa0a).
The study pins QuEST v4.2.0 commit 9d7618d7 and Aer 0.18.4; no vendor
source is included in the package.

## Prototype

Research-only, outside the Python runtime package. One packed operation
array is derived from the authoritative native circuit via public API.
One C ABI call for an entire execution, not per gate or amplitude.
C++ calls QuEST's existing specialized kernels, not custom simulation.
CPU-local complex128 buffer copies use documented CPU storage only; no
GPU/distributed assumptions. Native global phase is applied to output.
Strict allowlist of 11 native standard gates (H/X/Y/Z/RX/RY/RZ/CX/CZ/
SWAP/P), no unbound/dynamic circuits or arbitrary custom instructions.
Open controls rejected; unsupported operations fail explicitly.
QuEST environment initialized once per process, serialized bridge calls.
No public backend selection or automatic fallback.

## Experimental protocol

Compare Statevector, current Ketary, Aer (prepared/end-to-end, fusion
on/default and off), QuEST (prepared/end-to-end). Identical complex
initial vectors, gate order and global phase, double precision, CPU.
Check every supported gate on every basis vector at width 3, then random
circuits with complex normalized input at 4–22 wires. All output
amplitudes must match within 1e-9, not just probabilities.
Record 30 randomized samples, medians/p95 and raw times per workload.
Separate QuEST allocation/input, gate execution, export/destruction,
packing, NumPy copy and Result validation/copy diagnostics. Record
machine and dependency versions. Three thread-count jobs use separate
shared CI hosts; compare engines within each job, do not claim measured
thread scaling across different hosts. No performance guarantee.

## Next decision gates

1. Confirm compilation, exact mathematical equivalence, memory safety
   and scope of the bridge. Review all remaining logical gate semantics
   before proposing a runtime adapter. Pin ABI and review upstream license.
2. Compare native Aer end-to-end and prepared execution; optimize native
   boundary rather than adding a second model. Investigate batching,
   fusion, packed instructions and result ownership only where profile
   confirms cost.
3. Measure peak RSS in isolated workers and dedicated-host thread scaling.
   Preserve public Result defensive ownership; any private ownership
   transfer needs explicit proof that data has no aliases.
4. GPU/NUMA/MPI and native Rust/PyO3 construction are separate hypotheses.
   Do not replace Qiskit representation, use private Rust ABI, or change
   default execution from the current reference without an ADR, full
   compatibility checks and explicit owner decision.
