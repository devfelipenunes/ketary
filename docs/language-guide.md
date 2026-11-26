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
r.test.expectations({q.X(0) @ q.X(1):1,q.X(2) @ q.X(3):1}).require()
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
contract=c.contract(expectations={q.X(0) @ q.X(1):1})
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
assert report.phase==.375
```

Symbolic targets also accept reusable symbolic blocks without binding first:

```python
theta = q.Circuit.parameter("theta")
layer = q.Circuit.symbolic(2).ry(theta, 0).cx(0, 1)
template = q.Circuit.symbolic(4).apply_each(layer, placements=[(0, 1), (2, 3)])
result = template.bind(theta=.3).run()
```

`apply`, `apply_each` and `repeat` preserve native parameter identity. A
reused parameter is shared, not cloned into independent layer parameters.
Use distinct explicitly named parameters when independent weights are
needed. Same-name distinct native parameters fail before mutation. Unbound
blocks require an explicitly symbolic target; ordinary bound circuits and
classical circuits do not accept them. All native symbolic composition is
staged on an independent copy; source blocks remain unchanged. `compose`,
execution and logical serialization still require fully bound parameters.
Existing expansion bounds and wire ordering apply unchanged.

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

For end-to-end mathematical calibration run `python research/complete_workflows.py`. See the [developer pilot protocol](developer-pilot.md) for a separate formative human evaluation; no participant results yet.


## Mathematical expressions: real Pauli observables

```python
import ketary as q
H = 0.5*q.Z(0) + 0.8*(q.X(0) @ q.X(1))
r = q.bell().run()
energy = r.math.expectation(H)
variance = r.math.variance(H)
r.test.expectation(H, 0.8).require()
```

An Observable is an immutable bounded real Pauli sum; it does not execute
a circuit or represent a new gate. X/Y/Z/I use absolute wire indices;
shorter expressions pad identities on the left, preserving little-endian
order. Addition/subtraction and real scalar multiplication combine terms.
The @ operator is restricted to tensor products with disjoint nonidentity
wire support, not general matrix multiplication: overlapping support is
rejected even when the factors commute. Complex coefficients, arbitrary
matrices, exponentiation and synthesis are outside this API. Maximum 62
declared wires, 256 terms, 4096 product pairs. Zero retains its declared
embedding width. Explicit conversion via to_dict(width) or
to_qiskit(width) returns independent representations.

Expectation delegates to existing real weighted Pauli evaluation;
variance uses the existing streamed implementation and its default
resource limits. Explicit dense/streamed variance methods accept the
same Observable and expose their existing budgets. Observable expectations
may exceed [-1,1]; single Pauli checks retain that interval. No automatic
resimulation, no new state engine, no change to logical circuit replay.

The [core API](core-api.md) is the recommended entry path. Aggregate expectations accept immutable Observable keys or legacy full-width strings; use an Observable rather than an unhashable local-wire mapping as a key. See the compatibility policy for retained aliases and report formats.


## Expressive composition and grouped mathematics

```python
import ketary as q
layer = q.Circuit(4).apply(q.bell(), wires=[0, 1]).h([2, 3])
c = q.Circuit(8).apply_each(layer.repeat(3), placements=[(0,1,2,3), (4,5,6,7)])
r = c.run()
xx, zz = r.math.expectations([q.X(0) @ q.X(1), q.Z(0) @ q.Z(1)])
```

Use apply(block, times=k) for mutating sequential repetition, repeat(k) for
an independent repeated circuit, apply_each for ordered placements. The
block is not a live reference; self-application snapshots its original
source once. Overlapping placements are applied in order, not in parallel.
All mappings and expansion limits are checked before mutation. Counts must
be positive integers. New expansion paths allow <=10,000 placements and
100,000 appended operations; legacy single apply is unchanged. Existing
replay, trace and simulation limits remain separate. Repetition is U^k,
not k independently prepared states. A phase change at any intermediate
placement invalidates target checkpoint names. repeat drops annotations.

Grouped expectations return a tuple in caller order for 1..32 observable
queries, accept strings/local maps/Observable, and evaluate each distinct
full-width Pauli label once per call. The default max_work is 64*1024**2
Pauli-state entries (unique labels times state dimension); it is not a
runtime or RSS guarantee. No rerun, no global cache, no verdict. Use
result.test.expectations for verification.

## Ordered topology and rotation layers

```python
import ketary as q
c = q.Circuit(4)
c.ry([.1,.2,.3,.4], c.wires)
c.apply_each(q.Circuit(2).cz(0,1), placements=q.ring(c.wires))
```

Topology helpers generate ordered logical pairs, not hardware couplings. `chain` uses adjacent pairs; `ring` closes the chain (at least 3 wires); `star` uses the first wire as center; `all_pairs` emits combinations in caller order (not both directions). At most 4096 distinct nonnegative indices and 10000 pairs. The target validates actual bounds. `rx/ry/rz/p` accept ordered sequences of angles aligned one-to-one with ordered wires, or the existing scalar broadcast. All values preflight before mutation; no implicit Cartesian product. See [circuit-writing study](circuit-writing-study.md).


## Ordered dynamic measurement and reset

```python
import ketary as q
c = q.Circuit.classical(3, 3)
c.x(2).measure([2, 0], [0, 2]).reset(c.wires)
c.measure(1, 1)
counts = c.run_shots(shots=256, seed=42).counts
```

Scalar calls are unchanged. For batch measurement, use two nonempty ordered
sequences of equal length; wires and classical destinations must each be
distinct within that call. No broadcasting or implicit measurement.
Reset accepts an ordered selection of distinct wires. All batch inputs
are validated before mutation; operations are appended in caller order
on a native copy and committed only on success. Repeated measurements,
overwritten classical bits and repeated resets remain expressible as
separate scalar calls. These operations require explicit classical mode;
execution remains a separate optional Aer operation. The existing 12-wire,
12-bit, 1024-instruction execution limits remain unchanged.


## Explicit ordered pairs

```python
c = q.Circuit(4).h(0).cx(pairs=q.chain(range(4)))
c.cz(pairs=q.ring(c.wires)).rzz(.3, pairs=q.star(c.wires))
```

Use `pairs=` on fluent cx, cy, cz, ch, swap, cp, crx/cry/crz,
rxx/ryy/rzz. Scalar calls and the scalar gates namespace are retained.
Pairs are ordered, distinct within each pair; repeated and overlapping
pairs are allowed and applied in caller order. At most 10,000 pairs
per call; validate all before mutation. Parameterized pair gates accept
one scalar real or explicitly symbolic angle for the whole batch.
No Cartesian product, scheduling, hidden execution, or implicit controls.
Bound mode appends directly through the native transaction; symbolic
and classical mode stage on a native copy.


## Native variational ansatz and parameter vectors

```python
weights = q.Circuit.parameter_vector("w", 4)
layer = q.Circuit.symbolic(4).ry(weights, range(4))
template = q.ansatz(4, rotations=("ry", "rz"), reps=2, prefix="a")
bound = template.bind([0.1] * len(template.parameters))
energy = bound.run().math.expectation(q.Z(0))
```

The ansatz delegates directly to Qiskit n_local. Rotation blocks are ordered
rx/ry/rz, CX entanglement is linear/reverse_linear/circular/full with native
ordering, and a final rotation layer is included. Limits: 2..62 wires,
1..64 repetitions, 4096 parameters and 10000 estimated instructions.
Independent templates with distinct parameters must use distinct prefixes
when combined in one symbolic target. Vectors are immutable tuples of native
Parameter objects. Ordered bind consumes exactly one finite value per native
parameter in Circuit.parameters order; mappings and named binding remain
supported. Binding returns a new bound circuit; no hidden execution or
classical optimizer. This is an experimental convenience for a subset of
n_local, not all Qiskit variational capabilities.
