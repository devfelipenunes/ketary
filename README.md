# Ketary

An experimental Python SDK for quantum programming, built on Qiskit.

**Status: experimental SDK development.** The interface is not stable, the production gate is open, and no package release is available. Ketary is licensed under Apache-2.0 (see LICENSE). Third-party licenses remain applicable. No PyPI release is authorized.

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

## Documentation

- [Tutorial](docs/tutorial.md)
- [How-to guides](docs/how-to.md)
- [API reference and limits](docs/reference.md)
- [Explanation](docs/explanation.md)
- [Architecture](docs/architecture.md)
- [Engineering audit](docs/audit-l0.md)

## Scope

- One Circuit API with 29 fixed logical gate types plus bounded MCX, fluent aliases and `.gates`, independent copies, composition and inverse.
- Ideal statevector execution with explicit initial states, terminal sampling, pure-state math and checks; separate opt-in local dynamic execution.
- Explicit amplitude/probability, Pauli expectation, deterministic Born-rule explanation, logical resource reports and native text drawing. No hardware cost estimate.
- Rotation signatures are `gates.rx(theta, wire)`, `ry`, and `rz`; angles are finite real radians. `circuit.append(native_gate, wires)` accepts the supported gate subset; open controls are rejected. Symbolic construction is explicit and requires complete binding before unitary execution.
- Trace is explicit and bounded; decomposition only lowers SWAP in this spike.
- `Circuit.classical` supports a bounded single classical register, mid-circuit measurements, reset and conditional X/Z using the optional Aer extra. Bound unitary imports reject classical bits, unbound parameters, layout and metadata. No hardware or independent compiler.
- Qubit zero is the least significant bit. Preserve global phase; state fidelity alone does not prove operator equivalence.
- A memory guard estimates dense statevector payload, not total process memory. Probability and sampling dictionaries also have a configurable outcome cap.

## Quantum checks

```python
a = q.bell()
b = q.bell().gates.z(0)
a.run().test.distribution(b.run()).require()  # equal Z-basis probabilities
assert a.test.equivalent(b).status == "FAIL"  # different complete operators
a.run().test.expectation("ZZ", 1).require()
```

Checks return PASS, FAIL or UNSUPPORTED; `require()` raises on either non-pass result. State comparison may ignore global phase; complete operator comparison preserves it by default. Operator checks are limited to eight qubits and an explicit two-matrix payload budget. Invalid arguments raise errors. No implicit circuit execution occurs in operator checks or Result checks.

## Trace diagnosis

```python
reference = q.bell().gates.x(0)
observed = q.bell().gates.z(0)
diagnosis = observed.debug.compare(reference)
print(diagnosis.step_index, diagnosis.check.status)
```

Comparison is explicit, by equal gate indices on equal-width, equal-length circuits. The caller must establish meaningful alignment. A mismatch identifies the first observed state divergence, not necessarily its root cause. Matching traces do not prove operator equivalence. The comparison guards the combined snapshot payload and the per-trace step limit before evolving either circuit.

## Deutsch-Jozsa

```python
oracle = q.parity_oracle("101")
circuit = q.deutsch_jozsa(oracle)
result = circuit.run()
print(result.math.marginal_probabilities([2, 1, 0]))
```

The explicit oracle acts on n input wires and target wire n. The caller promises a reversible bit-flip oracle for a constant or balanced Boolean function. Ketary does not verify that promise or infer a general oracle from a Python callable. Provided constant and parity factories satisfy it. A zero input-register outcome indicates constant under that promise; nonzero indicates balanced. Marginal labels follow the supplied wire order, and all queries reuse the same state snapshot.

## Logical optimization

```python
c = q.bell().gates.x(0).gates.x(0)
optimized = c.optimize()
c.test.equivalent(optimized).require()
print(c.resources.summary(), optimized.resources.summary())
```

This explicit, nonmutating optimization cancels adjacent inverse pairs on identical ordered wires. It preserves global phase, does not apply approximate rotation cancellation or commute gates, and never runs a simulation. It is not device-aware transpilation. Reduced gate count is not a measured hardware speedup.

## Circuit replay

```python
payload = q.bell().gates.z(0).to_json()
restored = q.Circuit.from_json(payload)
restored.test.equivalent(q.bell().gates.z(0)).require()
```

The version-1 JSON format records producer versions, global phase, width and the supported ordered gate sequence. It preserves logical semantics, not native register names or annotations. Parsing is strict, allowlisted and bounded to 1 MiB, 22 qubits and 10,000 gates. No execution, pickle, eval, filesystem access or callable deserialization occurs. Producer versions are recorded for reproduction, not a cross-version numerical guarantee. Run and sampling remain explicit; store seeds alongside replay cases.

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

The public import remains `import ketary as q`. Internal modules separate circuit construction, Qiskit validation, result math and checks, trace, resource guards, and state factories. The developer expansion remains experimental; see the roadmap for its exact contracts and limits. Internal modules are not a second public API.

## Developer SDK expansion (experimental)

See [SDK roadmap and usage](docs/sdk-roadmap.md) for fluent gates, explicit initial states, mathematical reports, bounded algorithms and remaining boundaries.

Try the [developer notebook](examples/quantum_engineering.ipynb) for a complete ideal-state workflow.

The optional `dynamic` extra enables bounded local native Aer shot execution (`Circuit.classical`, `run_shots`, and teleportation). It is not part of the pure-state core. No hardware or package publication is authorized.

See [experimental verification engineering](docs/verification-roadmap.md) for bounded comparison, reproducible evidence, statistical contracts, and query plans. No universal guarantee from selected inputs.
