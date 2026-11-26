# Ketary API decision policy

Baseline: 077462c8. Issues #204–#211 refine #105/#134/#164/#196.
One Python facade; four concepts: Circuit, Result, Observable, Contract.
This policy is an engineering review tool, not a runtime layer or a release
stability guarantee. No public symbol is removed or renamed.

## Lifecycle and canonical language

Every declared entry is classified in api-lifecycle.json and cross-checked
with api-surface.json. Core (94), Advanced (170), Native (9), Compatibility
(34): 307 declarations including types and accessors, not 307 algorithms.
Core remains the learning path. Advanced is supported when its distinct
semantics matter; Native is explicit interoperability. Compatibility stays
callable and typed but is not taught as a parallel API. Candidate research
is not installed.

| Intent | Canonical route | Keep distinct |
|---|---|---|
| Build | Circuit(n), fluent gates | named algorithm factories for exact promises |
| Select | ordered wires, pairs=, chain/ring/star/all_pairs | absolute observable indices vs ordered local selection |
| Compose | apply(block,wires=...,times=...), apply_each | compose/inverse/repeat independent transforms |
| Parameterize | symbolic(), parameter/vector, bind | sweep_rows/sweep are independent runs, not sequential layers |
| Express math | Observable, X/Y/Z/I, evolve(H,time=...) | evolve exact commuting numeric; explicit approximation separate |
| Execute | run(), run_shots() | ideal pure vs empirical measured distributions |
| Read | result.math.expectation/probability | no simulation; bounded dense/streamed variance paths |
| Assert | result.test.expectation(...).require() | contract(...).verify(result) for reusable requirements |
| Diagnose | circuit.test.compare(), evidence | full operator/selected input/external/dynamic scopes not interchangeable |
| Interoperate | to_qiskit/from_qiskit, explicit transpile | no automatic engine or opaque compiler |

Do not promote an alias just because it saves tokens in one example.
Keep q.grover/q.qft/q.phase_estimation and other existing factories for
their documented promises. Existing compose vs apply is not redundancy:
one is independent and one mutates. Similarly sweep vs repeated apply,
sample vs measured shots, and assertion vs query have different semantics.

## Decision rubric

Hard gates: strict semantic oracle, bounded resources/ownership,
compatibility and typing, approved scope, exact-head CI. Unknown or failed
gates prevent promotion. A score never bypasses a gate.

For candidate prioritization, rate each dimension 0 (negative), 1 (mixed
or bounded evidence), 2 (positive), null (unknown):

| Dimension | Weight | Evidence |
|---|---:|---|
| Mathematical intent | 25 | removes accidental mechanics; preserves assumptions |
| Cross-family reuse | 20 | at least two materially different workflows for a new general primitive |
| Source complexity | 15 | executable before/after, AST and lexical data; retain losing cases |
| Computational cost | 15 | matched phase, common basis, build/run and memory; explain regressions |
| API consistency | 15 | extends canonical grammar, explicit mutation/modes/errors |
| Maintenance | 10 | implementation/test/doc burden and native dependency scope |

Score = sum(weight * rating / 2). If any rating is unknown, report no
complete score; do not replace unknown with zero. >=75 suggests promotion
review, 50–74.9 refinement, <50 recipe or defer. These are engineering
heuristics, not measured usability or statistically validated thresholds.
Existing supported APIs remain compatible independently of scores.
Record review decisions and evidence in api-decisions.json; update
when new experiments contradict the assessment.

## Parameter grammar

| Shape | Meaning |
|---|---|
| rx(theta, wire) | one angle on one wire |
| rx(theta, wires) | broadcast scalar, ordered distinct wires |
| rx(angles, wires) | one angle per wire, zipped |
| rzz(theta, pairs=edges) | one scalar per ordered pair |
| rzz(angles, pairs=edges) | aligned per-pair angles; repeated pairs intentional |
| apply(block,wires=...,times=k) | sequential repetition of one logical block |
| apply_each(block,placements=...) | sequential ordered remapping |
| bind({Parameter: value}) | native identity; complete independent bound copy |
| bind(*, name=value) | unique names; complete binding |
| bind(values) | native circuit parameter order, not insertion order |
| sweep_rows(rows) | independent fully bound circuits per ordered row |
| sweep(**columns) | zipped columns, not Cartesian product |
| evolve(H,time=t) | numeric time; exact commuting real Pauli evolution |

No implicit Cartesian product, implicit parameter sharing, implicit
partial bind, automatic ancilla, execution during construction, or
automatic approximation. Prefer Parameter identities for reusable
templates, names for simple interactive use, and ordered vectors when
their order is explicitly known. A same-name distinct identity must not
be silently renamed. Symbolic parameter expressions are supported in
symbolic gate builders; evolve's time remains numeric. A future symbolic
time design must qualify phase expressions, overflow and replay first.

## Candidate decisions

- Retain aligned pair rotations and exact evolve: integrated #199/#201.
- Prefer recipes over generic layers, graph-state aliases, alternate
  conjugation and additional sequence/power names.
- Refine controlled blocks in research; preserve relative phase and
  reduce synthesis cost before adding a general control method.
- Continue scoped preparation, arithmetic and truth-table oracle
  research. No automatic state reset, hidden ancillas or implicit synthesis.
- Explicit product formulas require a separate approximation contract.
- Defer automatic uncomputation; dirty-input counterexample remains.

Evidence: #200 13-task ladder 604/500/306/531 tokens (scalar/fluent/intent/
Qiskit), all 195 common-basis gates. #203 exact evolution 204 vs 474
manual tokens, 92 vs 72 native basis gates; public construction beat
prototype but not manual. #202 aligned CP/RZZ improved SDK construction,
not universally native Qiskit. Shared CI/authored cases are diagnostic.
Human/agent evaluation, dedicated hardware and post-merge visibility
remain open. Do not claim independent validation.

## Changes

Every new or modified public entry needs a canonical intent, exact
signature/mode, ownership, resource budget, semantic oracle, invalid
inputs, compatibility, stub/inventory/lifecycle coverage, executable
examples, and full CI. Use the smallest compatible change. No new
runtime dependency, second IR, generic DSL, or publication from this policy.
