# Full maturity audit — baseline 4df47937

## Scope and evidence
Reviewed the 26 runtime modules by explicit import/definition inventory and
selected high-risk paths; this is a static review, not line-by-line formal
verification or an independent review. Baseline #236 six jobs passed.
Core: 1244 passed, 27 Aer-only skips, 25 warnings; 3103 statements,
126 missed, 1118 branches, 93 partial, 95% combined. Dynamic: 1282 passed,
no skips, 25 warnings, 95%. Counts from candidate 82dc4aaa; merged tree
differs only by README and maturity-review documentation. Push CI not
visible through the connector. Challenge #231: 100 authored instances;
not 100 algorithms or an independent usability experiment.

## Conceptual architecture
Retain Circuit, Result, Observable, Contract; one Qiskit authoritative
model, explicit construction/execution/verification. Native optional
Aer and QCEC isolated; QuEST remains research. No second mutable IR,
generic backend interface, DSL, automatic approximations, or publication.
The public facade need not mirror private module boundaries. _circuit
(870 physical lines), _result (535), _algorithms (432), _ergonomics
(272), _verification (248), _trace (230) have concentrated responsibilities.
Run python -m research.architecture_inventory for AST inventory, local
and eager imports, SCCs and largest functions. Existing module-map count
needs reconciliation: 26 runtime modules, not 25. Avoid aesthetic splits;
prioritize a private synthesis boundary for _evolve if profiling and
dependency tests justify it. Keep numeric/ordered validation foundational.

## Correctness and resource findings
| ID | Evidence or hypothesis | Priority / action |
|---|---|---|
| A01 | _classical.run_shots sums values and calls len(label) before validating type; _statistical likewise sums malformed values | P0; #237 candidate checks mapping, labels, integers before arithmetic; malformed fixtures |
| A02 | _plan stores logical JSON, parses it in estimate and decodes it each run | P1; measure preparation, replay and query separately against explicit one-run reference; native snapshot only if immutability and bounds preserved |
| A03 | Result.sample full width allocates probability and multinomial arrays even for few shots | P1; measure peak RSS and time; preserve seed/reproducibility contract, no silent sampling change |
| A04 | SweepPlan binds every row separately; #234 removed row-column-row conversion, 25/27 median wins vs emulated prior path | P1; isolate native binding/validation costs, all-row preflight and ownership |
| A05 | _evolve pairwise commutation checks and per-term lowering; 88 vs 72 common-basis gates on 12-case corpus | P1; diagonal parity reuse and strict phase study, separate from public API |
| A06 | Native gate validation relies on pinned standard class and metadata allowlist | P0; adversarial custom gates/parameter/phase fixtures, preserve strict import boundary |
| A07 | compare selected-input scope and dense/operator scope differ | P0; challenge negative controls, evidence replay, never promote samples to proof |
| A08 | _Math expectation checks imaginary magnitude and finite real; nonfinite imaginary handling warrants explicit sentinel | P1; test injected malformed native return before altering code |
| A09 | Reports retain mutable dictionaries for compatibility | P1; audit defensive exports and evidence hash integrity; no breaking schema change |
| A10 | 25 warnings, mostly sparse SciPy diagnostic and intentional nonfinite fixture | P1; classify and remove avoidable sparse conversion from benchmark, assert intentional warnings |
| A11 | Optional Aer skipped 27 core tests; dynamic job passes all | P1; preserve distinct scope and record explicit skip reasons, not a blanket 100% claim |
| A12 | Public examples mostly small authored cases | P0; held-out workflows and external participants, record completion/repair/cost; no fake user evidence |

## Usage depth and potential abstractions
Evaluate full workflows rather than just individual gate calls:
- weighted multi-layer QAOA: objective, independent rows, verification;
- VQE: noncommuting energy, variance, repeated objective evaluation;
- arbitrary subsystem Hamiltonian composition and observable measurement;
- controlled blocks including relative phase, arithmetic and oracle;
- syndrome experiments with logical superpositions, dynamic results;
- injected phase defects, diagnosis and reproducible evidence.
For each, retain executable source, independent oracle, Qiskit idiom,
token/AST metrics, common-basis depth/gates, raw build/run timings, failures.
Source length is not readability or independent productivity.
Study ordered Observable remapping in research before deciding whether
a method is justified: current local circuit apply can remap evolution,
but measuring the corresponding observable requires manual labels.
Study parameter gradients only with occurrence/chain-rule semantics:
a shared parameter is not generally eligible for a naive two-point
parameter shift. Keep product preparation, truth oracles, arithmetic and
controlled blocks in research until distinct reuse and native cost evidence.
Keep topology/composition aliases out; existing primitives suffice.
No general QEC, hidden ancillas, hardware execution or silent approximations.

## Performance experimental matrix
| Layer | Variables | Evidence needed |
|---|---|---|
| Build | gates, scalar/aligned, prefix length, bound/symbolic | native sequence equality, p50/p95 raw samples |
| Bind | parameters, shared expressions, rows | separate assignment/validation, finite expression, source unchanged |
| Synthesis | Pauli support, terms, commuting topology | strict full operator, common basis, relative phase |
| Execute | width, depth, gate mix, initial state | same input/output, native pre-expanded and library baseline |
| Read | probability, grouped Pauli, density, sample, query plan | one explicit simulation, copy ownership, payload and RSS |
| Verify | selected input, full operator, trace, external | compare identical semantic scope, time/memory budgets |
| Native research | QuEST prepared/direct/fused, CPU threads | exact pinned ABI, matched output, isolated host; no automatic promotion |
Use shared CI diagnostic timings, never universal speed claims. Dedicated
authorized host, process RSS, isolated threads, all raw repetitions remain
outstanding. 16*2^n state bytes and 16*4^n per operator exclude scratch.
At 22 wires state payload is 64 MiB; at 8 wires one operator is 1 MiB.

## Priorities and release gates
P0: count boundary, strict mathematical and ownership regressions,
complete architecture inventory, real workflow validation, reconcile
existing QA/RF/CH issues by bounded acceptance rather than mass closing.
P1: measured resource paths, local Hamiltonian/observable reuse study,
synthesis refinement, source rewrite comparisons and warning audit.
P2: independent developers/agents, pinned external circuit corpus,
dedicated host and broader native backend qualification. All remain open.
Release requires integrated tree/CI, third-party notice review,
controlled evidence and explicit owner decision; no release or version bump.
