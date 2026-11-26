# Ketary

**Write quantum programs you can understand and verify.**

Ketary is an experimental high-level Python SDK for building, understanding and
verifying small quantum programs. It uses Qiskit for the authoritative circuit
and ideal-state execution model. Python stays Python; no separate language or
compiler is required.

```python
import ketary as q

circuit = q.bell()
result = circuit.run()
XX = q.X(0) @ q.X(1)

result.test.expectation(XX, 1).require()
print(result.math.probabilities())
```

## Build. Understand. Verify.

Build a circuit with fluent gates, analyze an independent snapshot using
mathematical expressions, and state which numerical properties must hold.
For example, a phase error can preserve measurement probabilities:

```python
expected = q.bell()
observed = expected.copy().z(0)
contract = expected.contract(expectations={q.X(0) @ q.X(1): 1})

contract.verify(expected.run()).require()
assert contract.verify(observed.run()).status == "FAIL"

report = observed.test.compare(expected)
if report.evidence is not None:
    report.evidence.reproduce()
```

The counterexample is specific to a failing input; the report does not prove
root cause. Matching samples alone do not prove operator equivalence.

## Get started

Python 3.12.x only. From a verified local checkout:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install .
python examples/first_verification.py
```

**Pre-alpha:** version 0.1.0.dev0, experimental API, no PyPI release.
No hardware execution, general compiler, or claim of formal verification.

## One API, progressive control

| Concept | Purpose |
|---|---|
| Circuit | Construct and compose a program |
| Result | Inspect a reusable ideal-state snapshot |
| Observable | Express real Pauli mathematics |
| Contract | Reuse explicit numerical expectations |

Advanced capabilities (symbolic sweeps, named selections/checkpoints, debugging,
replay, resources, optional dynamic Aer execution) are available when needed.
Native interoperability is explicit. Existing aliases continue to work.

- [Getting started](docs/getting-started.md)
- [Core API and design principles](docs/core-api.md)
- [Tutorial](docs/tutorial.md)
- [How-to guides](docs/how-to.md)
- [Language guide](docs/language-guide.md)
- [Mathematical guide](docs/mathematical-guide.md)
- [Verification guide](docs/verification-guide.md)
- [API reference](docs/reference.md)
- [Architecture and decision records](docs/architecture.md)
- [Complete surface map](docs/api-surface.md)
- [Known limitations](docs/known-limitations.md)
- [Compatibility policy](docs/compatibility.md)

## Development and validation

Use the pinned Python version and constraints from the repository.
See [release validation](docs/release-validation.md) for exact test,
benchmark and packaging commands, and [architecture](docs/architecture.md)
for boundaries. All changes go through CI-gated pull requests. No release or
dedicated-host performance claims are made.

Apache-2.0; see LICENSE and [third-party review](docs/third-party-review.md).
