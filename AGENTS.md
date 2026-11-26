# Ketary development instructions

- Treat this as an experimental Qiskit-backed SDK, not a released package.
- Target Python 3.12.x only during initial development. Use .python-version as the CI and local version source; future packaging must declare >=3.12,<3.13 until support is deliberately expanded. Do not add a Python version matrix.
- One public Python programming interface, with progressive access through namespaces. Factories return Circuit. Qiskit QuantumCircuit is authoritative; do not implement a second production simulator.
- Builder gate operations mutate explicitly; transforms return copies; Result is a reusable defensive snapshot. Do not silently re-run simulations. Keep debug and costly analysis opt-in.
- Preserve global phase and Qiskit little-endian qubit numbering. Reject unsupported operations explicitly. Compare operators in context, not only one output state.
- Validate the small PoC first: execute all tests and independent Qiskit probes; fix failures before benchmarking. Do not skip required checks or loosen oracles to get green CI.
- Benchmark equivalent workloads; record versions, raw timings, median/p95, and peak RSS separately. Do not claim a speedup without evidence.
- Production gate: validated PoC, benchmark, RFC review and explicit approval. Later extend gates, math, algorithms, sampling/primitives, tests, diagnostics and visualization in separate PRs.
- No new DSL, CLI, separate compiler, alternative quantum SDK, hardware execution or publishing in the initial scope. Apache-2.0 is proposed in the draft PR; preserve third-party notices. Final release approval remains pending.
- Use English in code and public documentation. Do not put private workspace links, credentials, personal information or internal notes in this public repository.
- Never merge automatically or push changes directly to main. Record actual test results and limitations in each PR.
