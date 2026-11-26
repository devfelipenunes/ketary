# Ketary

An experimental Python SDK for quantum programming, built on Qiskit.

**Status: design spike.** The interface is not stable, the production gate is open, and no package release is available. Ketary is licensed under Apache-2.0 (see LICENSE). Third-party licenses remain applicable. No PyPI release is authorized.

## Try the proof of concept

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q -rs tests research/probes
```

Run from the repository root. Python **3.12.x** is the sole supported development target, with Qiskit 2.6.2. The `.python-version` file defines the CI target. Earlier Python 3.11 results are historical, not a continuing support commitment.

```python
import ketary as q

circuit = q.bell()
result = circuit.run()
result.test.probability("00", 0.5).require()
print(result.math.probabilities())

circuit.gates.z(0)
print(circuit.debug.trace()[-1].result.math.statevector())
```

The result is a snapshot. The second operation does not change the earlier result. The two Bell states have equal computational-basis probabilities but different relative phase.

## Scope

- One Circuit API: construction, H/X/Y/Z/S/T/SDG/TDG/RX/RY/RZ/CX/CZ/SWAP/CCX, Bell/GHZ, import/export, composition and inverse.
- Ideal statevector execution, terminal sampling, pure-state math and checks.
- Explicit amplitude/probability, Pauli expectation, deterministic Born-rule explanation, logical resource reports and native text drawing. No hardware cost estimate.
- Rotation signatures are `gates.rx(theta, wire)`, `ry`, and `rz`; angles are finite real radians. `circuit.append(native_gate, wires)` accepts the same supported gate subset; unbound parameters and open controls are rejected.
- Trace is explicit and bounded; decomposition only lowers SWAP in this spike.
- No classical bits, mid-circuit measurement, reset, layout, metadata, unbound parameters, hardware, alternative SDK or independent compiler.
- Qubit zero is the least significant bit. Preserve global phase; state fidelity alone does not prove operator equivalence.
- A memory guard estimates dense statevector payload, not total process memory.

## Validation

Run all tests, including upstream Qiskit probes. Missing Qiskit is a failure, not a passing skip. Historical local PoC results are not evidence of this branch's CI.

```bash
python -m pip freeze > environment.txt
python benchmark.py > benchmark_results.json
```

The diagnostic benchmark uses paired randomized timing, mixed gate workloads and isolated peak RSS processes. It runs after required tests in CI. Shared runner results are preliminary, not release guarantees; build and execution costs are reported separately. User ergonomics and broader workload coverage remain to be measured. No performance claim is made.

## Examples and review

Run `python -m examples.first_bell` and `python -m examples.diagnose_phase` from the repository root. These executable examples illustrate the same API. See `docs/validation.md` for the performance and human usability protocol.

## Workflow

All changes go through branches and pull requests. Merge reviewed changes only after required CI passes and within owner authorization. Do not bypass checks or publish packages without explicit authorization.

## Local distribution builds

Install `build` and run `python -m build` to produce a local wheel and source distribution. The version `0.1.0.dev0` is an internal development identifier, not a published release. CI installs both artifacts in clean environments outside the checkout. Use `pip install .` for a local installation with runtime dependencies only.

## Internal architecture (experimental)

The public import remains `import ketary as q`. Internal modules separate circuit construction, Qiskit validation, result math and checks, trace, resource guards, and state factories. No new capability or production-readiness claim follows from this refactor. Internal modules are not a second public API.
