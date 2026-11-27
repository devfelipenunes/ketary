# QContract Alpha — 121-delivery execution register

Snapshot: baseline A4 ee3699a5; comparative lab 3e4487b2; contract-first integration candidate pending exact-head CI. Status E = evidence for the stated task/scope, I = partial or implemented candidate, P = pending, X = blocked on external participation/hardware. No item marked E on implementation alone. For release gates, only exact-head validated results count; prototype evidence is not public API readiness.

| ID | Status | Task | Evidence / next action |
|---|---|---|---|
| A01 | E | exact A4 artifact and namespace audit. | A4 exact-head three-platform qualification 46078771325; original artifact audit |
| A02 | E | complete #528 required checks and dependency audit, inspect failures. | 32 exact-head successes including dependency/SDK; R30 macOS-14 cancellation documented, R31/macOS-15 and A4 all platforms passed; repository accepted merge |
| A03 | I | merge preserving ancestry; verify main tree and post-merge gates. | #528 merged b8ba69f8; A4 ancestor, main identical tree, post-merge execution not confirmed |
| A04 | E | close only #512–527 confirmed ancestors; no branch deletion until review. | #512 auto-merged, #513–527 closed after verified ancestry and explanatory comments; no branch deletion |
| A05 | I | separate runtime, independent checker, adapter and lab boundaries; inventory imports. | A4 wheel AST audit; runtime audit candidate |
| A06 | P | canonical package source layout, avoid generated AST extraction long term; parity with A4. | Not completed; follow master roadmap acceptance criterion |
| A07 | P | move legacy SDK adapters out of runtime; stable internal packed representation. | Not completed; follow master roadmap acceptance criterion |
| A08 | I | architecture ADR and supported gate/domain/limit matrix. | Candidate CI architecture and domain reference |
| A09 | I | stable versioning/changelog and backwards compatibility decision. | Candidate 0.1.0a3 version; changelog/compatibility still pending |
| A10 | P | public namespace/license review, no registry upload without owner approval. | Not completed; follow master roadmap acceptance criterion |
| D01 | I | named transition with before/after, preserve existing Contract API. | Named transition candidate API |
| D02 | I | invariant constructor and explicit all-input scope. | Invariant candidate API |
| D03 | I | zero-input stabilizer constructor and scope contrast lesson. | Zero-input constructor and example |
| D04 | I | clean-ancilla constructor with explicit initialized-input assumptions. | Clean ancilla constructor |
| D05 | I | named plan, bounded batch, duplicate names rejected, no hidden resource increase. | Plan and nonempty bounded outcome |
| D06 | I | explain() meaningful status, domain, route, snapshot and obligation. | Outcome.explain and reference |
| D07 | I | require() rejects FAIL, INCONCLUSIVE and UNSUPPORTED distinctly in text. | Strict require policy |
| D08 | I | public type design, static checker and width-safe Pauli labels; wire-order tests. | Updated stubs and wire-order tests, width-bound type deferred |
| D09 | I | typed local Pauli builders X/Z/Y(wire), tensor and signs without ambiguous label order. | pauli_on explicit indexed terms (tensor builder pending) |
| D10 | I | rational sums ergonomic constructors and canonicalization. | Existing exact fractions; example only, new ergonomic constructor pending |
| D11 | I | clean-input equivalence/action and strict phase named forms. | Named wrapper covers relative/equivalence; convenience forms pending |
| D12 | I | separability cuts and Z branch probability/unnormalized expectation vocabulary. | Domain reference and small tests; new vocabulary pending |
| D13 | I | noise and QEC vocabulary; code-only vs circuit-bound explicit. | Domain reference and examples; public vocabulary pending |
| D14 | I | structured result/error classes, machine-readable diagnostics, no bool ambiguity. | Structured named Outcome and explicit statuses; dedicated errors pending |
| D15 | I | minimal counterexample explanation incl. basis axes and exact residual. | Existing witnesses and explanatory metadata; minimality not proven |
| D16 | P | explicit composition and stage refinement with sound propagation of assumptions. | Not completed; follow master roadmap acceptance criterion |
| D17 | P | immutable plan and versioned, canonical JSON representation; safe schema validation. | Not completed; follow master roadmap acceptance criterion |
| D18 | I | pytest integration, strict CI policy with explicit unsupported/inconclusive behavior. | pytest CI guide, candidate strict require tests |
| D19 | P | optional decorator syntax experiment; no implicit hardware run or hidden work. | Not completed; follow master roadmap acceptance criterion |
| D20 | I | execution bridge example: same immutable snapshot, verify before executing, reject mismatch. | Tutorial specifies re-prepare after edit; actual execution bridge pending |
| D21 | P | compare current constructor vs named/fluent/decorator styles with users; choose one primary syntax, avoid redundant public DSLs. | Not completed; follow master roadmap acceptance criterion |
| D22 | I | API acceptance: all ten families, valid/invalid examples, typed API, understandable errors, no private imports. | Ten-family candidate qualification staged; CI pending |
| T01 | I | one command local install on each qualified OS; clean environment tutorial. | A4 wheel install guide; 0.1.0a3 candidate pending |
| T02 | I | first proof with H, one Pauli, predicted outcome. | H tutorial and executable test |
| T03 | I | Bell correlations, deliberate phase mutation, all-input vs zero-input example. | Bell and domain contrast candidate example; earlier prototype passed |
| T04 | I | ancilla leak example and clean uncomputation. | Ancilla cleanup tutorial/test |
| T05 | I | distinguish phase-insensitive equivalence and strict equality. | Strict/phase explanation and strict control; extended lesson pending |
| T06 | I | demonstrate non-Clifford limits, INCONCLUSIVE is not FAIL. | Budget lesson and examples |
| T07 | I | QEC code/error set and measurement instrument examples. | Finite QEC and branch tests plus domain reference |
| T08 | I | pytest + GitHub Actions minimal integration guide. | How-to guide and tested require policy; external pytest workflow pending |
| T09 | I | reference per contract: signature, equation, scope, resources, examples, limitations. | Initial all-domain reference; complete per-contract reference pending |
| T10 | I | explanations: Pauli matrices, signed masks, conjugation, tableau, Q(sqrt2), exact vs numerical. | Initial explanation of signed Pauli, scope, exact math |
| T11 | I | flow diagrams and notebook exercises: predict, run, inspect, modify, explain. | Predict-modify-explain tutorials; notebooks and diagrams pending |
| T12 | I | troubleshooting, error glossary, FAQ, migration from old API. | How-to troubleshooting initial text; glossary/migration pending |
| T13 | I | run every tutorial in CI from installed wheels; no stale notebooks. | Candidate tests hooked into qualification; full tutorial extraction pending |
| T14 | I | documentation built under Diataxis (tutorial/how-to/reference/explanation). | Diataxis docs structure created; candidate content pending review |
| T15 | P | first-contract target <10 min as study hypothesis, measure not assert. | Not completed; follow master roadmap acceptance criterion |
| B101 | E | cached inverse Clifford comparison, preserve raw samples and losses. | B1 exact-head 3e4487b2, artifact 15236732444: 3780 checks/144 scenarios |
| B102 | E | state comparisons vs StabilizerState and inverse (not dense only). | Artifact 15236517759: 448 comparisons/10 scenarios |
| B103 | E | fix pauli-prop tuple and truncation handling; 30 near-Clifford cases. | Artifact 15237526085: 90 decisive comparisons, zero discarded norm |
| B104 | P | add numerical preparation split vs prepared operator propagation; no numerical result promoted to exact. | Not completed; follow master roadmap acceptance criterion |
| B201 | E | batched exact Clifford state expectation prototype (48 cases, thresholds). | Artifact 15236617536: 10082 checks/48 exploratory scenarios; prototype only |
| B202 | E | profile losing 2-wire/64-contract Python report workload. | Same artifact: cProfile, 500 batches of 64 contracts |
| B203 | I | integrate state route only after independent replay, full status/expectation parity and no budget borrowing. | New default-state batch candidate and independent replay; parity tests submitted |
| B204 | I | optional compact diagnostic/verdict mode; never map INCONCLUSIVE to false property. | Status-only candidate returns all four outcomes, no evidence; parity tests submitted |
| B205 | I | slots/validated immutable plans, eliminate duplicate hashing/admission, compare to A4. | Avoid hashes/expansion in status-only route; immutable plan; other allocations pending |
| B206 | P | packed batch and SIMD/lookup select only where measured useful. | Not completed; follow master roadmap acceptance criterion |
| B207 | I | micro/macro profiling (FFI, hashing, report, preparation, allocation), inspect negative cases. | cProfile confirms hashing and report overhead; broader FFI allocation profiling pending |
| B208 | I | paired held-out comparisons and regression gate. | Candidate paired timing and held-out matrix checks pending CI |
| B301 | I | T-count 0/4/8/12/16/24/32, depth, support size, topology and T density. | Initial 0/4/8/16/32 T corpus; more depth/topology/density needed |
| B302 | I | Aer MPS, stabilizer, extended stabilizer and statevector comparisons at matched accuracy. | MPS and dense baseline validated; extended stabilizer pending |
| B303 | I | disconnected factorization, low entanglement, high entanglement, graph/brickwork/Ising. | GHZ and local graph baseline plus coverage-repair experiment; wider topologies pending |
| B304 | I | term growth, cone reduction, cancellation, block-Clifford aggregation, exact arithmetic limits. | 16 inconclusive high-T obligations identified; alternative exact DAG experiment staged |
| B305 | P | >64 multiword representation feasibility; only Alpha blocker if declared support demands it. | Not completed; follow master roadmap acceptance criterion |
| B306 | I | coverage/time/memory curves, timeout and inconclusive counts. | 184/200 B3 exact coverage measured; memory/time bounds pending |
| B401 | I | GHZ/BV/Deutsch-Jozsa, phase kickback, QFT Clifford+T subsets, arithmetic/uncomputation. | Initial GHZ/BV/uncompute corpus validated; remaining algorithms pending |
| B402 | I | QCEC equivalence with semantic mutants, equal rewrites, phase changes, dense small oracle. | 18 small QCEC/Operator cases validated; complex mutants/phase variants pending |
| B403 | P | use public held-out MQT/real Qiskit circuits within admitted alphabet; provenance and license. | Not completed; follow master roadmap acceptance criterion |
| B404 | P | transpile before/after, preserve strict phase decision; no silent approximate transpilation. | Not completed; follow master roadmap acceptance criterion |
| B405 | I | mutation operators: wrong wire/gate/sign/control, dropped entangler, missing uncompute; label equivalent mutants. | Initial phase/sign and X mutant controls; larger mutation set pending |
| B406 | I | record sensitivity, false positives, inconclusive rate and coverage; no false verdict in corpus. | Initial 9+9 equivalence corpus correct; broader sensitivity pending |
| B501 | E | exact rational Pauli sums vs dense operator. | Artifact 15237590853: finite rational sum matrix controls |
| B502 | E | finite Pauli mixtures vs matching density-channel model; no general CPTP claim. | Same artifact: finite Pauli-mixture matrix controls |
| B503 | E | Z measurement branches, branch probability and unnormalized expectations, zero-probability cases. | Same artifact: all four Z branch controls including zero probability |
| B504 | I | stabilizer code commutation/independence and recovery table, repetition/Steane examples. | Repetition-code exact condition and mutant validated; Steane pending |
| B505 | I | partial replay limitations per domain; compare independent algorithms when available. | Existing selected replay; new state replay candidate; coverage matrix pending |
| B601 | I | benchmark manifest seeds, versions, source SHA, CPU/threads/affinity, host isolation. | Shared CI commit/host/dependency samples recorded; controlled host settings pending |
| B602 | P | fixed dedicated CPU, repeated fresh processes, warm/cold, p50/p95 and confidence intervals. | Not completed; follow master roadmap acceptance criterion |
| B603 | P | peak RSS and logical budget accounting; actual subprocess timeout/memory limits. | Not completed; follow master roadmap acceptance criterion |
| B604 | I | matched outputs and comparable setup, record negative results, held-out seeds. | B1 matched outputs and loss reporting; held-out/corpus extensions pending |
| B605 | X | independent replication on controlled hardware (requires access); shared CI not certification. | Requires controlled dedicated hardware and independent replication |
| B701 | E | design external evaluation against pytest/Qiskit, tasks and consent protocol. | External evaluation protocol created; no recruitment or study results |
| B702 | I | usability tasks: first contract, diagnose mutation, ancilla, integrate CI; compare syntax options. | Study tasks and counterbalancing specified; actual participant testing pending |
| B703 | X | record completion, time, errors, perceived ease, learning, not only satisfaction. | Requires participant data; cannot fabricate |
| B704 | X | recruit 5–10 external developers and two reviewers; no invented participants or results. | Requires consenting real developers and reviewers |
| B705 | P | anonymized evidence, publish limitations and changes; adoption is not guaranteed. | Not completed; follow master roadmap acceptance criterion |
| B706 | I | scientific contribution matrix against QBricks/QbC/Hoare/Stim/QCEC/QuCheck and related work. | Prior art and positioning initial analysis; full contribution matrix pending |
| C01 | E | inspect 32 research-related workflows in candidate; 31 broad/narrow research and alpha entries. | Artifact 15237416418: 32 files inventory |
| C02 | E | repeated broad path triggers and repeated native builds identified. | Same artifact: 31 broad research triggers, 24 files with build command |
| C03 | I | inventory test entrypoint, domain, oracle, fixture, mutation, platform, dependency and runtime. | Static workflow inventory and group mapping; executable ID-level map pending |
| C04 | I | map coverage to replacement tests; exact independent oracles and negative controls mandatory. | Candidate coverage migration groups; prove replacement parity first |
| C05 | I | retain legacy SDK regression and native dependency audit required checks. | Existing dependency and SDK checks retained; complete exact-head results pending |
| C06 | I | build once per OS/ABI/commit; reuse verified artifacts, not cross-commit binaries. | Shared-build pilot passed (one build, eight consumers); broader OS reuse pending |
| C07 | I | group short core tests; parallelize independent expensive suites; measure queue vs execution. | Eight parallel pilot consumers; queue/execution analysis pending |
| C08 | I | PR fast gate: admission, exact math, witnesses, replay, FFI, public smoke, typing, examples, dependency audit. | A4 smoke and new candidate API/replay tests; unified fast gate pending |
| C09 | I | research extended gate: historical R5–R32 corpus, differential/metamorphic, resource/security and algorithms. | Historical tests retained, migration map created |
| C10 | I | performance separate workflow; manual/controlled trigger, not unconditional on docs changes. | Separate comparison workflow pilot passed; release policy pending |
| C11 | I | nightly/release full historical regressions and reproducibility; keep old evidence. | Historical regressions/reproducibility preserved; scheduled policy pending |
| C12 | P | branch protection inventory and stable required check names before narrowing filters. | Not completed; follow master roadmap acceptance criterion |
| C13 | P | explicit always-run aggregator; skip optional jobs with documented dependency mapping. | Not completed; follow master roadmap acceptance criterion |
| C14 | I | concurrency per workflow/ref for superseded commits only; never cancel a final candidate blindly. | Superseded comparison runs concurrency group implemented; full ref policy pending |
| C15 | I | pin actions/dependencies and read-only permissions; no publishing credentials in tests. | Pinned actions and read-only permissions in pilot; full inventory pending |
| C16 | I | compare old/new exact-head test IDs, verdicts, failure injection, time and compute; no weaker coverage. | Pilot passed; exact historical coverage comparison and failure injection pending |
| C17 | P | only then disable redundant automatic triggers, archive scripts and remove unreachable runtime modules. | Not completed; follow master roadmap acceptance criterion |
| C18 | I | no blanket deletion, no removal of unique mathematical or security coverage, preserve rollback. | Historical tests and branches retained; no deletion |
| C19 | I | target: >=50% fewer redundant builds and >=30% PR wall time reduction; measure actual results. | 7/8 lab build reduction by design, no measured total duration target yet |
| C20 | P | release gate includes all required checks and slow-suite exact head, regardless of fast CI outcome. | Not completed; follow master roadmap acceptance criterion |
| M01 | I | exact semantic specification for each domain, proof sketches, assumptions. | Initial reference and explanation; full proofs and domain review pending |
| M02 | I | independent replay for newly optimized state route and mixed requests. | Candidate independent state replay and mixed-status controls |
| M03 | I | witness verification and adversarial tampering, canonical IDs and scope binding. | Candidate replay tamper and provenance tests; full adversarial coverage pending |
| M04 | I | distinguish invalid evidence, unsupported replay and insufficient budget. | API docs distinguish None and False; dedicated evidence statuses pending |
| M05 | I | domain admission and strict builtin validation, bounded resource extraction. | A4 strict admission; candidate invalid input cases |
| M06 | I | no arbitrary Python sandbox claim; inspect custom gate normalization and concurrency. | Scope and concurrency limits documented; further adversarial checks pending |
| M07 | I | differential/property-based fuzz, shrink counterexamples, persist regression fixtures. | Seeded differential checks and known high-T cases; shrinker pending |
| M08 | I | memory, time, coefficient growth and logical budget audit; no false precision. | B3 coverage audit, logical budgets documented; real limits pending |
| M09 | I | dependency vulnerabilities, SBOM/NOTICE, build provenance and legal review. | A4 dependency audit retained; final SBOM/legal review pending |
| M10 | I | portable Linux/macOS/Windows artifact matrix; test oldest declared targets; Python/ARM scope explicit. | A4 all three OS; oldest supported target matrix incomplete |
| M11 | I | deterministic pure Python wheel cross-host, native reproducibility per target and independent builds. | A4 pure Python wheel equality and native prior same-host tests; independent target builds pending |
| M12 | I | reproducible docs, API stubs, sdist/wheel and packaging from clean checkout. | Stubs and executable docs staged; sdist/package source layout pending |
| M13 | I | contribution guide, license, security reporting, scope/limitations and changelog. | Initial docs and limitations; contribution/security/changelog pending |
| M14 | P | signed/tagged local Alpha candidate only after owner approval; no public registry reservation. | Not completed; follow master roadmap acceptance criterion |

## Totals
121 deliveries: 14 evidenced, 83 partial/candidate, 21 pending, 3 externally blocked. Counts describe work packages, not test count or release percentage. Reconcile on each exact-head run.

#528 merged at b8ba69f8f7eea5e76abc44b2f351f6659ed8e5e9; #529 merged at 49cff9d31590cb19369c66afabf8bd9d60b177ea; main tree matches the validated research head 3e4487b2. #530 retargeted to main. #528 tree identical to main at verification; post-merge run not confirmed. Preserve prior exact-head artifacts and historical workflows until CI coverage migration is verified.


## Consolidation checkpoint — 530

Validated #529 exact head 3e4487b2 (2/2 workflows, including shared
build plus 8 consumers) merged with history into main at
49cff9d31590cb19369c66afabf8bd9d60b177ea. Compare original head to main:
0 missing commits, 0 changed files. #530 is now directly based on main.

#530 initial head 005e2cb912e6e6a5f7098a165a529b98d279fba6:
comparative run 46083586008 passed all 10 jobs. Artifact 15238107081
contains 16 high-T cases, 64 properties per strategy: default 48
decisive, plain 57, phase-weighted 57. 162 decisive replay successes
across three strategies; 9 recovered obligations, 7 still unresolved
by both DAGs (local-graph). Setup medians 0.19591/19.7095735/43.4182965
ms; query medians 1.3084765/1.766577/1.862587 ms. Explicit DAG selection
retained; no automatic retry or increase of logical budgets.
Artifact 15237697798: default full state reports win 10/10 vs cached
inverse values, median 4.6857x; 10/10 vs StabilizerState, 10.9106x.
Artifact 15238385926: public full reports win 42/48 vs Qiskit inverse
expectations, median 2.3558x. Outputs differ (full report vs numeric
values); shared hosts, not a general speed claim.

Isolated qualification run 46083586009 failed on all three platforms.
Linux trace: dispatch_parity.py line 72, mixed-report equality with
per-item check. The new state route was used only in all-state batches;
mixed queries still went through the older state path. Fix 589091b:
preflight the entire mixed batch with qualified31.validate, route
eligible state obligations together, preserve original per-item quota,
delegate remaining items at q * remaining_count, restore order.
Pure and mixed eligible state obligations use same route; low budgets
and explicit DAG policies retain prior behavior. New regression
7c604af includes transition + two states with distinct costs + sum,
budget boundaries and invalid input in mixed batch. The failing
original regression remains unchanged. This is a candidate correction,
not a confirmed fix. Do not merge #530 before new exact-head results.

No status inflation: 14 evidenced, 83 partial/candidate, 21 pending,
3 external blockers remain the conservative register classification.
A3 post-merge qualification, all runtime API tests, broad CI cleanup,
controlled hardware and external user studies are not closed.


## Frozen 0.1.0a3 candidate — final package evidence

Exact head `bc16ff0b74d7766d483a5bccd7258d998826c8b3`, run 46084014830:
3/3 platforms passed. Original artifacts 15238856035 (Windows), 15238562005
(Linux), 15237893203 (macOS). Independent wheel SHA-256 and every RECORD
entry checked: six wheels, 144 RECORD rows including RECORD self-entries.
Per host: 55 smoke, 8978 dispatch parity, 1040 comparison, 2195 contract-first
checks; 12268 executions, 36804 total. MyPy positive and expected negative
cases passed. Python wheel SHA-256 identical on all three:
`3118ff1ad3a8ab45c87ba321a34efd667628fdb86ec992e58ddc97485273bdf4`.
Comparative run 46084014678 passed 10/10 jobs. Mixed-batch correction validated.
Native wheel hashes differ per target as expected. Linux tested glibc 2.35,
macOS 15 ARM64, Windows AMD64, CPython 3.12. No older OS/other ABI guarantee.

Scope frozen: no expansion of gate alphabet, contract types, research corpora,
architecture or hardware support. Existing historical tests remain unchanged.
At documentation preparation, 31/33 workflows passed, 1 legacy SDK workflow
was running (benchmark job), 1 R30 historical macOS-14 job cancelled. The
separate native-dependency workflow is not triggered by this candidate;
comparison against qualified A4 confirms no pyo3, native staging or audit
workflow source changes, and current SDK dependency-review passed.
Do not imply a new native dependency audit executed at this head.
No public tag, publication or general formal verification claim.
