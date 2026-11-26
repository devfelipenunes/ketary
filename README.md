# Ketary

An experimental Python SDK for quantum programming, built on Qiskit.

**Status: design spike.** The interface is not stable, the production gate is open, and no package release is available. This repository does not yet have an approved open-source license. Licensing will be resolved before distribution.

## Try the proof of concept

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q -rs tests research/probes
```

Run from the repository root. Python 3.11 and 3.12 are candidate CI versions. The Qiskit pin is an experimental baseline to be verified.

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

- One Circuit API: construction, H/X/Z/CX/SWAP, Bell/GHZ, import/export, composition and inverse.
- Ideal statevector execution, terminal sampling, pure-state math and checks.
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

The preliminary benchmark measures timing only, after tests pass. Peak RSS, randomized paired measurements and broader workloads are future validation tasks. No performance claim is made.

## Workflow

All changes go through branches and pull requests. Do not merge automatically. Review evidence and production readiness before expanding scope or publishing.
