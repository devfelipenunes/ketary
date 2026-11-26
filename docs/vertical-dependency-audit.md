# Vertical dependency audit

Baseline 2d87a8bb. Evidence: PR #331 SDK run 45780564351, jobs
139774714996 (dependency), 139774714755 (dynamic), 139774715241
(external), 139775304754 (build). These are candidate logs, not push CI
for the combined tree. Observed closures: runtime 7, validation 17,
dynamic 11, external 10 (old collector omitted extras), build 31.
All four audit jobs reported no known vulnerabilities in the scanned
versions. Not a security or legal certification.

## Findings
- Qiskit 2.6.2 metadata requires numpy>=2.0,<3, scipy>=1.14,
  rustworkx>=0.15, dill>=0.3, stevedore>=3 and typing-extensions.
  NumPy 2.5.5 and SciPy 1.18.1 were resolved; the latter requires
  numpy>=2.0,<2.8. Ketary's declared lower NumPy floor is not the
  effective floor. Do not claim independent NumPy 1.x compatibility.
- Rustworkx and SciPy both depend on NumPy. Aer adds psutil,
  python-dateutil and tzdata in this resolution. MQT adds mqt-core
  and nanobind-backend. The latter had no discovered dist-info notice
  in the old inventory: review actual wheel/upstream notices.
- Build tools are separate. Certifi/pathspec MPL-2.0 declarations,
  docutils mixed classifiers and bundled numerical notices require
  review if redistributing; no assertion that the SDK wheel inherits
  these licenses. The existing wheel audit checks membership.
- The old walker evaluated only extra=""; it did not traverse
  requested extras on roots or transitive requirements. Correct this
  by unioning extras per canonical package and revisiting on growth.
  This is metadata closure, not a lockfile, binary SBOM or resolver.
- Research imports SciPy and audit imports packaging directly.
  Declare them in requirements.txt, without expanding runtime roots.
  Keep Python 3.12 and Qiskit pinned; no dependency version upgrade.

## Vertical execution map
Circuit -> validation -> native QuantumCircuit gate methods (Rust-backed
representation, Python entrypoint) -> _execution.execute_ideal ->
Statevector.from_instruction/evolve -> NumPy arrays -> Result._from_evolution.
Fresh owned contiguous writable arrays are adopted only when not aliases
of borrowed input; public construction and exports retain defensive copies.
Binding uses native assign_parameters then validates finite angles and phase.
Chunked variance uses NumPy XOR/parity/gather rather than repeated per-wire
evolve; sampling preserves seeded native multinomial. Do not equate Rust
circuit storage with a fully Rust statevector simulator.

## Low-level research
- IBM Qiskit C API https://quantum.cloud.ibm.com/docs/en/api/qiskit-c/index :
  same Rust internals for transpilation, different entrypoints. In Python/C
  hybrid mode IBM recommends Python transpilation; C transpiler can assume
  C-exposed constructs. Do not blindly bypass native validation or lower
  arbitrary Python-created circuits via C.
- NumPy show_runtime https://numpy.org/devdocs/reference/generated/numpy.show_runtime.html :
  record actual SIMD and BLAS/LAPACK configuration, not assumptions about
  OpenBLAS, AVX or MKL. show_config records build configuration.
- QuEST https://github.com/QuEST-Kit/QuEST : MIT, native simulator,
  optional OpenMP/MPI/CUDA/HIP/cuQuantum. Existing research bridge pinned
  to a revision; compare direct/prepared/lowered modes, strict phase and
  output ownership. Do not promote it or claim GPU measurements.
- Profile validation, native assignment, evolution, adoption and public
  export separately on matched inputs. Dedicated CPU and RSS qualification
  remain open (#100 #101 #246 #300 #301 #310). License review #110 remains
  open; no publication or new runtime dependency.
