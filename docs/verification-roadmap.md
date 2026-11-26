# Verification engineering roadmap (R01–R15)

Experimental SDK-only scope. Qiskit is authoritative. No implicit execution,
AI/MCP, hardware, formal-proof claim or public release.

| ID | Candidate delivery | Boundary |
|---|---|---|
| R01 | Runtime capabilities, measurement provenance, preserved API | Static mode-specific typing remains a future RFC |
| R02 | Shared predicate evaluation | Legacy dictionary and typed report scopes retained |
| R03 | 32 seeded circuit cases, independent native operator and complex-state oracles | Not exhaustive, external bug corpus pending |
| R04 | Elementwise, Frobenius, spectral norm and process fidelity | Dense 8-wire cap; phase aligned by overlap, not optimized spectral norm |
| R05 | Selected product states then optional complete numerical check | No sample-only universal PASS |
| R06 | Structural, zero-input distribution/state and operator diff | No inferred causal diagnosis |
| R07 | Immutable hashed JSON witness, explicit reproduction, version metadata | Hash not authentication; only input counterexamples |
| R08 | Explicit index-to-Contract checkpoints | Zero-input, stops at first nonpass, no persistent annotations |
| R09 | Bounded product-state counterexample search | No exhaustive or entangled input search |
| R10 | Bounded greedy observed-gate deletion preserving a witness | Not globally minimal, not root cause, may remove correct operations |
| R11 | Simultaneous Hoeffding intervals, PASS/FAIL/INCONCLUSIVE | IID shots, fixed hypotheses, specified outcome marginals only |
| R12 | Immutable explicit query plan, one run and payload estimate | Not a compiler/sweep optimizer, no implicit caching |
| R13 | Incremental checkpoint cursor and streamed Pauli variance | Work/payload caps; no speedup assertion |
| R14 | Explicit optional QCEC adapter, bounded worker deadline | Different external phase relation; no auto promotion into ladder |
| R15 | 24 matched public calibration cases, Qiskit and optional QCEC | Not independent benchmark, no general superiority claim |

## Semantics

`a.test.compare(b)` uses strict phase by default. State L2 failures are
counterexamples to the requested norm bound. Ignoring phase uses per-input
overlap alignment, which cannot establish one common phase. Full numerical
PASS is based on the operator norm under the declared alignment; it is not a
formal proof. Sample-only matching and unavailable dense checks are
INCONCLUSIVE. Dense FAIL may have no product-state witness. QCEC is a
separate opt-in method, not used to assert strict-phase Ketary equivalence.

`Evidence.from_json` parses bounded versioned data, never executes it.
`reproduce` explicitly reruns two circuits; producer match is reported,
not assumed. Greedy minimization preserves the same input and tolerance
against a fixed reference; it is not program repair. The serialized content
hash detects accidental changes, not malicious rewriting.

Shot intervals use radius sqrt(log(2k/alpha)/(2N)); a union bound covers the
k declared Bernoulli events simultaneously under IID sampling. PASS requires
the entire interval in the target tolerance band; FAIL requires disjointness.
Neither means exact probabilities or hardware correctness. Untouched classical
bits are rejected. Do not adapt hypotheses after observing the same sample.

## Example

```python
import json
import ketary as q
a = q.Circuit(1).z(0)
b = q.Circuit(1)
report = a.test.compare(b, inputs=["0", "+"])
assert report["status"] == "FAIL"
artifact = q.Evidence.from_json(json.dumps(report["evidence"]))
assert artifact.reproduce()["reproduced"]
```

## Reproduction and comparisons

```sh
python -m pytest -q tests research/probes
python research/verification_comparison.py
# Separate trusted environment for optional native comparator:
python -m pip install 'mqt.qcec[qiskit]==3.12.0'
python -m pytest -q tests_external
python research/verification_comparison.py --external
```

The public calibration creates 12 equivalent circuits with adjacent inverse
pairs and 12 non-equivalent X mutants. All are authored, three-wire cases;
Qiskit Operator.equiv is an external API oracle, not independent hardware.
Raw single-run timings are diagnostic, not controlled performance evidence.
External status is reported without conflating probably_equivalent with PASS.
The external dependency is not part of the SDK distribution requirements;
its isolated job records inventory and vulnerability results.

Prior work: [MQT QCEC](https://mqt.readthedocs.io/projects/qcec/en/stable/equivalence_checking.html),
[MQT Debugger](https://mqt.readthedocs.io/projects/debugger/en/latest/),
[QuCheck](https://arxiv.org/abs/2503.22641). These ideas have substantial
precedent. Future validation: held-out real bugs, mutation operators,
scalability, paired repeated timings/RSS on dedicated host, and developer
evaluation. No claim of novel verification methods or improved productivity.

## Public-report adaptations and scaling

Six independently authored unitary cases drawn from Bugs4Q-indexed public reports (bit order, accidental builder accumulation, Bell preparation, Fourier sign, ancilla uncomputation and controlled-wire mapping) plus one dynamic reset/uncompute adaptation. Sources: https://github.com/Z-928/Bugs4Q and individual links in research/public_defect_cases.py; dynamic source https://quantumcomputing.stackexchange.com/questions/5959. These are **adaptations**, not full historical reproductions or an unbiased bug sample. Analytic tests check expected amplitudes and bit order. CI reports detection, witness reproduction and positive controls. No original code copied.

research/verification_scaling.py measures raw repeated timings, median/p95 and per-method worker process high-water RSS (excludes QCEC subprocess memory) on GHZ circuits at widths 2–20. Dense (<=8), selected states (<=12) and optional QCEC (<=20 in this study) have different semantics. Sample-only matches remain INCONCLUSIVE. No speedup conclusion across unequal guarantees. Dedicated host results remain a separate requirement.
