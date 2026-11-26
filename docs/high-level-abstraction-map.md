# High-level abstraction inventory — ABS01–ABS36

Baseline: main 628d5467 (PR #45 integrated), public stub, canonical Core API
and architecture audit. Design proposals only; this document does not add
methods or approve expansion. Scope is patterns exposed by the current SDK,
not every possible quantum-language feature. Existing examples are marked
available; candidate spellings require review and testing.

## Reference patterns

- [Qiskit QuantumCircuit](https://qiskit.qotlabs.org/docs/api/qiskit/qiskit.circuit.QuantumCircuit):
  composition, repetition, broadcast, tensor.
- [Cirq CircuitOperation](https://quantumai.google/reference/python/cirq/CircuitOperation):
  repeated reusable subcircuits and qubit mappings.
- [PennyLane Catalyst release notes](https://docs.pennylane.ai/projects/catalyst/en/stable/dev/release_notes.html):
  adjoint/control and compiled control flow; not equivalent to Ketary's
  static expanded construction.
- [Qrisp conjugation](https://qrisp.eu/reference/Quantum%20Environments/ConjugationEnvironment.html):
  compute/action/uncompute pattern; automatic uncomputation is out of scope.
- [PyTorch vmap](https://docs.pytorch.org/docs/stable/generated/torch.vmap.html):
  map intent instead of explicit iteration; no vectorization/speed claim.
- [NumPy broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html):
  deliberate shapes and explicit broadcast rules.

## Inventory

Status: Available = documented existing feature; Candidate = assess design
and oracles; Defer = substantial new semantics or redundant spelling.
P0 = first design cycle, P1 = subsequent justified design, P2 = optional.
All candidate syntax is illustrative.

| ID | Pattern | Preferred API or design candidate | Status |
|---|---|---|---|
| ABS01 | Repeat same block sequentially | apply(block, times=k), default 1 | P0 candidate |
| ABS02 | Independent repeated circuit | block.repeat(k) if a distinct use case warrants it; same internal expansion | P1 candidate |
| ABS03 | Apply same block to several ordered wire groups | apply_each(block, placements=[(0,1),(2,3)]) | P0 candidate |
| ABS04 | Single-wire broadcast | c.h([0,1,2]), c.ry(theta,wires) | Available |
| ABS05 | Pairwise two-wire operations | apply_each(q.Circuit(2).cx(0,1), placements=pairs); no ambiguous zip/cartesian broadcast | P0 via ABS03 |
| ABS06 | Chains, rings, stars, all-to-all | pure bounded ordered pair/group generators, passed to ABS03 | P1 candidate |
| ABS07 | Apply ordered heterogeneous blocks | use ordinary Circuit builder as a reusable composite; no separate Program/Layer object | Available |
| ABS08 | Disjoint tensor of blocks | apply_each with disjoint placements; optional independent tensor factory only if needed | P1 candidate |
| ABS09 | Full-width selection | read-only c.wires (range or tuple); evaluate against range(c.num_qubits) | P1 candidate |
| ABS10 | Named wire selections | c.register("data",range(n)); tuple slices | Available |
| ABS11 | Register-relative remapping | apply(block,wires=data); named selections are not allocated quantum variables | Available |
| ABS12 | Basis-state preparation | explicit x gates or run(initial_state="101"); possible basis-preparation factory (not arbitrary amplitudes) | P1 candidate |
| ABS13 | Inverse and adjoint | block.inverse(); strict global phase | Available |
| ABS14 | Compute/action/uncompute | compute_action_uncompute(U,V,compute_wires=...,action_wires=...) | Available |
| ABS15 | Apply inverse to selected wires | c.apply(block.inverse(),wires=...); avoid inverse keyword alias until needed | Available |
| ABS16 | Generic coherent controlled block | requires synthesis/phase/whitelist review, not mere sugar | Defer |
| ABS17 | Arbitrary Python or quantum conditions/while loops | Python control flow for static construction; existing restricted if_x/if_z dynamic; no new coherent control | Defer |
| ABS18 | Integer power syntax / dunder multiplication | prefer explicit repeat; do not overload @ or ** for circuits yet | Defer |
| ABS19 | Symbolic parameters and complete binding | Circuit.symbolic, Circuit.parameter, bind(theta=...) | Available |
| ABS20 | Zipped parameter sweep | c.sweep(theta=angles).run() | Available |
| ABS21 | Parameter rows and Cartesian grid | explicit sweep_rows(rows) or pure bounded row generation; no silent Cartesian expansion | P1 candidate |
| ABS22 | Aligned experiment results | explicit sweep evaluation with binding/result pairing, preserve .run tuple | P1 candidate |
| ABS23 | Execute same circuit for multiple input states | c.run_many(initial_states=...), explicit bounded independent simulations | P1 candidate |
| ABS24 | Execute heterogeneous circuits | Python collection/loop remains baseline; no job framework or implicit workers | Defer |
| ABS25 | Real Pauli algebra | q.Z(0)+.8*(q.X(0)@q.X(1)) | Available |
| ABS26 | Many expectations on same Result | r.math.expectations([A,B]) aligned tuple; distinct from r.test.expectations | P0 candidate |
| ABS27 | Grouped probability queries | r.math.probability(label), r.evidence(bits=...); consider typed ordered batch of selected labels | P1 candidate |
| ABS28 | Subsystem probabilities | r.math.marginal_probabilities(wires); no redundant probability alias | Available |
| ABS29 | Subsystem partition analysis | entropy(partition=...), schmidt(wires); consider complement helper, not new state type | P1 candidate |
| ABS30 | Targeted one-run queries | c.plan(bits=...,paulis=...,subsystems=...).run() | Available |
| ABS31 | Aggregate predicates | c.contract(expectations={H:...}); r.test.expectations(...); .require() | Available |
| ABS32 | Same contract at several checkpoints | current mapping {name:contract for name in names}; consider overload with explicit at=... only if common | P1 candidate |
| ABS33 | Compare and reproduce evidence | c.test.compare(reference); report.evidence.reproduce() | Available |
| ABS34 | Automatic decoder dispatch | keep explicit decode_* functions; avoid hidden algorithm metadata/automatic interpretation | Defer |
| ABS35 | Bulk measurement and reset | ordered (wire,bit) pairs, preflight all; dynamic only and separate from ideal Result | P1 candidate |
| ABS36 | Export/inspection/report shortcuts | existing to_qiskit/to_json/inspect/render; teach canonical paths rather than aliases | Available |

## First proposal: one composition grammar

```python
layer = q.Circuit(4).apply(q.bell(), wires=[0,1]).h([2,3])
c = q.Circuit(4).apply(layer, times=1000)  # proposed
```

Default times=1 preserves existing calls. Start with bound unitary mode only
and positive integer repetitions (reject bool); zero identity semantics
need explicit review. Validate mapping, total appended instruction count,
phase/annotations and resource budget before mutation. Source reuse is not
a live reference to mutable circuits. Preserve native ordered operation
sequence, not just zero-state probabilities. Self-application snapshots the
source. Ordinary errors restore prior suffix/phase/annotations. Do not
introduce a second IR or opaque instruction that breaks replay. Existing
to_json/trace/verification limits still apply even if construction succeeds.
The repeated operator is U^k, not k independent states or shots.

```python
c.apply_each(q.bell(), placements=[(0,1),(2,3),(4,5)])  # proposed
```

Ordered placements; validate all before committing. Overlap between groups
is allowed only under explicitly sequential semantics; "parallel" never
implies actual scheduling. Repeated wires within a single mapping invalid.
Topology helpers are classical ordered index generators, not a hardware
coupling map or routing compiler. Avoid a large family of gate-specific
times, all, ring, chain aliases.

## First proposal: grouped mathematical queries

```python
r = q.bell().run()
xx, zz = r.math.expectations([q.X(0) @ q.X(1), q.Z(0) @ q.Z(1)])  # proposed
```

Return aligned numeric values, not a verdict. No rerun, no silent sampling.
Bound number of terms, work and output. Validate before costly evaluation;
shared Pauli terms can be reused within a single call only, with no global
mutable cache. Existing r.test.expectations returns a VerificationReport,
not numeric values. Current individual calls remain supported.

## Acceptance and roadmap

1. ABS01/03/05: one private bounded composition expansion mechanism,
   reference loops, strict complete operators at small widths, full native
   sequence and phase on larger cases, overflow/rollback/self-apply, no
   new replay schema. Measure old loops vs new APIs with matching outputs.
2. ABS26: native/analytic expectation oracles, ordered results, validation
   before work, no simulation during snapshot queries.
3. ABS06/09/12/21–23/27/29/32/35: design review using existing workloads,
   demonstrate reduction in tokens, calls and new concepts before adding API.
4. ABS02/08: introduce independent transformations only if existing compose
   plus repeat cannot express the intent clearly.
5. Deferred: compiler, generic control synthesis, dynamic loops, arbitrary
   state preparation, auto-uncompute, hidden execution and operator-overload
   DSL. Keep ordinary Python for host control.

Require type/stub and inventory parity, compatibility, native mathematical
oracles, resource preflight, failure atomicity, CI and documented limits.
No new public API has been implemented by this mapping.

## Current architecture baseline

PR #45 exact head 596124b3 passed six CI jobs (495 core / 506 with Aer,
94% coverage, strict mypy) and merged at 628d5467 with identical tree.
[CI](https://github.com/devfelipenunes/ketary/actions/runs/45756745318)
shared-run medians for 1,000 repeated gates: historical batch copy path
749.036 ms vs new 22.845 ms; historical block composition 20.308 ms vs new
9.747 ms. Distinct matched native comparisons show remaining overhead:
2.726 vs 22.469 ms batch; 6.026 vs 9.554 ms block. Historical comparison
reconstructs the previous algorithm, not a separately installed old commit.
These are diagnostics, not controlled hardware results or general speed claims.

## First implementation candidate

ABS01/02/03/05/26 are implemented in the expressive composition PR, pending exact-head CI/review. Positive counts only; at most 10,000 placements and 100,000 appended operations for new expansion paths (legacy single apply unchanged). Independent repeat drops annotations. Grouped expectations allow 1..32 ordered queries with default 64 Mi-entry unique-Pauli state work budget; no RSS or speed guarantee. All other candidate items remain proposals.
