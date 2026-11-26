# Getting started: build, understand, verify

Ketary is an experimental Python 3.12 SDK on Qiskit. No public PyPI release.
Use an authorized local checkout or a verified artifact for the exact commit.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

From a verified local wheel use `python -m pip install /path/to/ketary-0.1.0.dev0-py3-none-any.whl`.
Do not install an unrelated package by name. Optional local dynamic execution
is available with `python -m pip install '.[dynamic]'` from the checkout.

## Build and verify

```python
import ketary as q

circuit = q.Circuit(2).h(0).cx(0, 1)
result = circuit.run()
XX = q.X(0) @ q.X(1)
result.test.expectation(XX, 1).require()
print(result.math.probabilities())
```

The first line constructs the program, run explicitly simulates it, and
the snapshot is reused. XX describes an observable, not an operation
applied to the circuit. H and CX create an ideal Bell state.

## Understand a failure

```python
expected = q.bell()
observed = expected.copy().z(0)
good, bad = expected.run(), observed.run()

contract = expected.contract(expectations={XX: 1, "ZZ": 1})
contract.verify(good).require()
good.test.distribution(bad).require()
assert contract.verify(bad).status == "FAIL"

report = observed.test.compare(expected, inputs=["00"])
assert report.status == "FAIL"
evidence = report.evidence
assert evidence is not None and evidence.reproduce()["reproduced"]
```

Equal computational-basis probabilities hide the relative phase error.
The observable detects the difference, and the explicit comparison saves
a failing-input witness. Reproduction is an explicit execution; it does
not prove root cause. No hidden simulation occurs when accessing a report.

The same diagnostic is executable with `python examples/first_verification.py`;
CI runs it from a clean installed wheel outside the checkout.
Learn the [four core concepts](core-api.md), [mathematical conventions](mathematical-guide.md),
and [verification scopes](verification-guide.md) next.
