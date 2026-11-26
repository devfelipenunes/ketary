# PERF03: Qiskit C ABI / Rust fast path

Qiskit 2.6.2 has an official, experimental C ABI for Python extensions.
Use headers from qiskit.capi.get_include(), QISKIT_PYTHON_EXTENSION and
qk_import; no private Rust symbols or raw object-layout guessing.
See [IBM guide](https://quantum.cloud.ibm.com/docs/en/guides/c-extension-for-python)
and [QkCircuit](https://quantum.cloud.ibm.com/docs/en/api/qiskit-c/qk-circuit).

The isolated research extension constructs a native Rust circuit in one
C call via qk_circuit_gate then transfers ownership using
qk_circuit_to_python_full. Read-only packing borrows CircuitData using
qk_circuit_borrow_from_python and non-allocating instruction views. GIL
remains held; no borrowed view or pointer escapes; no in-place mutation
of the existing program. Native kind check rejects custom gates.
Only eight standard gates in this prototype; 100k operation cap.
The bytes protocol is private, native endian and not a persistence schema.
Pin 2.6.2; ABI remains experimental. No package runtime changes.

Benchmark 1k/10k/100k operations with 30 paired samples, compare native
sequence equality and a small strict operator, reject invalid rows and
unsupported instructions. The Python baseline consumes arrays and
per-gate dispatch; also measure alternative raw native public batching
for specific repeated workloads before choosing a product fast path.
Future integration could connect native read-only traversal to QuEST
without Python per-gate conversion. This remains a separate hypothesis,
not a validated runtime backend.
