# Binding finite scan and native-kernel feasibility

Refs #301 #310 #308 #102 #103. Investigate whether a compiled finite-value
scan justifies crossing the Python/native boundary. C++17 and Rust kernels
are research-only, compiled with ordinary optimizations (no fast-math).
NumPy is a vectorized comparator; explicit SIMD instructions are not
assumed or guaranteed. The kernels only check float64 finiteness; they
do not implement any quantum gate, simulation, or binding. No installed
library dependency, new backend, API, implicit dispatch or release.

Nine workloads use actual bound native Qiskit templates. Compare existing
complete validation with exact-float-only extraction, type validation,
conversion, finite scan and phase check; report prepacked scans separately.
Non-exact-float values are outside this prototype, not approved for bypass.
Validate zero, subnormal, extreme finite, NaN and infinities at multiple
positions before timing. Raw p50/p95, compiler and environment records.
Do not promote a fast prepacked kernel if end-to-end extraction/FFI costs
dominate. No dedicated-host or architecture-portability claim.
