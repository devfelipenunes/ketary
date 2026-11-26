# Getting started: build, understand, verify

Ketary is an experimental Python 3.12 SDK on Qiskit. There is no public PyPI
release. Use an authorized local checkout or an artifact from a successful CI
run of the exact commit you intend to evaluate.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

From a verified local wheel, use `python -m pip install /path/to/ketary-0.1.0.dev0-py3-none-any.whl`
instead. Do not install an unrelated package by name. The dynamic extra can
be installed from the checkout with `python -m pip install -e '.[dynamic]'`.

## Five-minute workflow

```python
import json
import ketary as q

expected = q.Circuit(2).h(0).cx(0, 1)
observed = expected.copy().z(0)
r = observed.run()
assert expected.run().test.distribution(r).status == "PASS"

contract = q.Contract(2, expectations={"XX": 1, "ZZ": 1})
assert contract.verify(r).status == "FAIL"
report = observed.test.compare(expected, inputs=["00"])
assert report["status"] == "FAIL"
evidence = q.Evidence.from_json(json.dumps(report["evidence"]))
assert evidence.reproduce()["reproduced"]
contract.verify(expected.run()).require()
```

The wrong circuit has the same Z-basis probabilities as the intended Bell
state, but a different relative phase. The XX expectation distinguishes the
states. The saved witness reproduces a specific failing input. It is not a
proof of the defect's cause. See [mathematics](mathematical-guide.md),
[verification](verification-guide.md) and [limits](known-limitations.md).

Run the same workflow with `python examples/first_verification.py` from
the checkout. CI executes this example using an installed wheel outside the
repository, with no optional simulator or external verifier.
