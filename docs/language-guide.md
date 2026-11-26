# Progressive Python language guide (experimental)

The same Circuit object owns a Qiskit QuantumCircuit. Use ordinary Python
functions for reusable blocks. There is no new parser, simulator, IR or
compiler. Prefer fluent gates and explicit run; legacy gates and analyze
remain supported.

## DX01–DX11

| ID | Candidate | Semantics |
|---|---|---|
| DX01 | Canonical style and 11 paired tasks | authored, not human data |
| DX02 | ComparisonReport, DiagnosticReport, StatisticalReport, OperatorMetricsReport, SemanticDiffReport | legacy dict subclasses, explicit status and scope; evidence property parses already recorded artifact |
| DX03 | Single-qubit fluent gates accept ordered wire iterables | atomic candidate copy; legacy .gates scalar; no ambiguous multi-wire broadcast |
| DX04 | apply(block,wires=...) | mutates atomically, compose still copies |
| DX05 | register(name,wires), registers | named tuples of existing indices, no allocation; aliases may overlap |
| DX06 | local Pauli mappings | canonical full-width label; identity allowed, no general operator algebra |
| DX07 | contract factory, grouped expectations, named checkpoints | no simulation on creation; check zero-input prefix |
| DX08 | named bind and zipped sweeps | 1–32 rows, <=12 wires/256 operations; explicit run; aggregate snapshot payload guard |
| DX09 | decoders for BV, QPE and teleportation | existing Circuit factory remains; modal estimate or empirical output, not generic solver |
| DX10 | signature parity, native operator checks, 11 paired examples | human validation and dedicated performance pending |
| DX11 | compute_action_uncompute | exact U,V,U^-1 sequence; not proof of ancilla cleanup |

## Construction

```python
import ketary as q
c=q.Circuit(4)
alice=c.register("alice",[0,1])
bob=c.register("bob",[2,3])
c.apply(q.bell(),wires=alice)
c.apply(q.bell(),wires=bob)
r=c.run()
r.test.expectations({"IIXX":1,"XXII":1}).require()
assert abs(r.math.expectation({0:"X",1:"X"})-1)<1e-9
```

Named selections are ordinary immutable tuples, not native quantum registers
or ownership tokens. Their order is the declared order. For marginal
probabilities this order determines the label; for composition it maps
block wire 0 to the first selected wire. A selection can be reused on a
different circuit if indices are valid. Copy preserves annotations; bind,
compose, inverse, optimize, decompose, transpile and logical replay produce
new circuits without annotations. An in-place apply that changes global
phase clears checkpoint names because phase is applied at the start of
the trace. No annotation changes the native operator or replay schema.

## Verification

```python
expected=q.bell()
observed=expected.copy().z(0)
report=observed.test.compare(expected)
if report.evidence is not None:
    assert report.evidence.reproduce()["reproduced"]
```

Reports preserve dictionary keys, mutation and JSON compatibility. Do not
use their truth value as a verdict; inspect status or call require().
A mutable report is not an authenticated record. SemanticDiffReport deliberately has no aggregate status; use its separate dimensions and operator report. Typed evidence access
does not rerun circuits. A comparison can FAIL without a product witness.
Sample-only matches remain INCONCLUSIVE.

```python
c=q.bell().checkpoint("entangled").z(0).checkpoint("changed")
contract=c.contract(expectations={"XX":1})
report=c.debug.verify_checkpoints({"entangled":contract,"changed":contract})
assert report.status=="FAIL"
```

Checkpoint names refer to the current append-only prefix; duplicate resolved
indices are rejected. They are not native instructions or causal diagnoses.

## Parameters and algorithm decoding

```python
theta=q.Circuit.parameter("theta")
template=q.Circuit.symbolic(1).ry(theta,0)
plan=template.sweep(theta=[0,.5,1])
results=plan.run()
report=q.decode_phase_estimation(q.phase_estimation(.375,precision=3).run(),precision=3)
assert report["phase"]==.375
```

Bind by native mapping or unique names, never both; use the native mapping if a parameter name conflicts with the bindings argument. Sweep columns are zipped,
not Cartesian; all rows are bound and serialized at planning time, without
simulation. Results are ideal snapshots, and bindings are available in row order.
Decoders reuse a snapshot or ShotResult; a unique modal outcome is not proof
of the algorithm promise, a tie is inconclusive. Teleportation decoder reads
the measured output bit, not fidelity. Simon's existing GF(2) recovery remains.

## Reversible composition

`c.compute_action_uncompute(U,V,compute_wires=...,action_wires=...)` applies
U then V then U inverse atomically. It does not assert that an ancilla
is returned to zero (V can disturb the computed data). Arbitrary controlled
block synthesis is deferred; preserve global phase and avoid silently
expanding the native gate whitelist.

## Evaluation

Run `python research/dx_comparison.py` for 11 paired authored examples,
token/call/numeric literal counts, full native operator or matched
result comparisons, and five equivalent native Qiskit snippets. Native source counts are shown only for these five tasks. These are not independent usability data. Some clearer
examples intentionally use more tokens; no claim of universal improvement.
No human or dedicated-host experiment has been completed.
