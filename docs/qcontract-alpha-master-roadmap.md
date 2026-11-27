# QContract Alpha master roadmap — contract-first engineering

Owner decision: aim for a usable community Alpha, not a general Qiskit
replacement. Preserve exact mathematical semantics, clear scope, and
honest inconclusive results. All P0/P1 work and B1–B7 are in this plan.
No task is complete solely because a test was written. Track each by
commit, artifact, covered domain, explicit limitations and acceptance gate.

## Baseline and execution gates

A4 #528 at ee3699a5fa79377ecae08ef29be08921b675c501:
run 46078771325 3/3 platform jobs passed. Original artifacts Linux
15235309347, macOS 15235499680, Windows 15237390033: each 55 smoke,
8978 report parity and 1040 Qiskit comparisons (30219 total executions).
All three Python wheels identical SHA256
23ffe8cf221ca4f90cb0823de1846b4de2b4a1ebb343c56f9049cb0fc7cac159,
native hashes match qualification metadata, MyPy positive/negative
passed, Linux audited manylinux_2_34 x86_64 and installed on glibc 2.35.
31 other workflows queued at inspection. No merge until required and
substantive regression checks pass; do not delete historical branches.

B1 #529 exact initial head ffb38e295b50c96c94bad5d5c649e181c17fd1e9,
run 46079730931: Clifford artifact 15237030868 3780 checks/144
scenarios; state artifact 15236281220 448 comparisons/10 scenarios.
Prepared inverse comparison median 3.053x (114/144 wins);
batch1 5.271x (36/36), batch8 3.647x (36/36), batch32 1.895x
(24/36), batch64 1.114x (18/36); end-to-end 3.868x (142/144).
Worst prepared ratio 0.309 (2 wires/512 gates/64/dense), i.e.
Qiskit ~3.24x faster. State default wins 4/10 vs cached inverse,
median ratio 0.8934; full DAG often slower than default. All 224
observables resolved by each of two native routes, 448 comparisons.
Near-Clifford failed because pauli-prop returns (operator, truncated
norm), not just operator. Fix committed 61cffe3; assert zero discarded
norm, preserve original failing evidence. No near-Clifford result yet.
B2 experiment d3ed670: state_batch_b2.py, exact batch expectation
prototype, 48 scenarios, same output comparison with Qiskit and
separate full reports; low budget and invalid inputs; cProfile.
Language prototype 701c8fe: named plans, explicit domains, explain,
strict require, Bell positive/mutant and budget/domain contrast.
Both are experimental, not yet public API or validated results.

## Methodology

Contract-first development: Specify -> Implement -> Verify -> Execute.
Inspired by Eiffel require/ensure/invariant, Python icontract/deal,
quantum Hoare logic, QbC refinement, QuCheck property testing and
MorphQ metamorphic testing. Do not equate observable conjugation
with arbitrary Hoare implications. A contract must state scope,
quantification, mathematical predicate, input requirements, evidence
and status. Keep all-input transition, zero-input state, clean-subspace,
strict vs phase equivalence, hypothetical measurement and finite error
set distinct. Execution stays with Qiskit/backend for Alpha; verification
never implies hardware error-free behavior.

Primary references:
https://www.eiffel.org/doc/eiffel/I2E-_Design_by_Contract_and_Assertions
https://icontract.readthedocs.io/en/latest/usage.html
https://pypi.org/project/deal/
https://arxiv.org/abs/2303.17750
https://doi.org/10.1145/3720433
https://doi.org/10.22331/q-2026-07-23-2172
https://arxiv.org/abs/2503.22641
https://ieeexplore.ieee.org/document/10172716/
https://doi.org/10.1145/3715106
https://diataxis.fr/
https://qiskit.github.io/pauli-prop/guides/quickstart.html
https://learn.github.com/well-architected/library/productivity/recommendations/effective-ci

## Work packages

Status: E = evidenced, I = implemented candidate awaiting validation,
P = planned, X = externally blocked. All exit criteria below are
requirements for Alpha or explicitly designated post-Alpha extensions.
No promise that all future research becomes release scope.

### A — integration, architecture and scope (P0)
- A01 E — exact A4 artifact and namespace audit.
- A02 P — complete #528 required checks and dependency audit, inspect failures.
- A03 P — merge preserving ancestry; verify main tree and post-merge gates.
- A04 P — close only #512–527 confirmed ancestors; no branch deletion until review.
- A05 P — separate runtime, independent checker, adapter and lab boundaries; inventory imports.
- A06 P — canonical package source layout, avoid generated AST extraction long term; parity with A4.
- A07 P — move legacy SDK adapters out of runtime; stable internal packed representation.
- A08 P — architecture ADR and supported gate/domain/limit matrix.
- A09 P — stable versioning/changelog and backwards compatibility decision.
- A10 P — public namespace/license review, no registry upload without owner approval.

### D — design by contract and usability (P0/P1)
- D01 I — named transition with before/after, preserve existing Contract API.
- D02 I — invariant constructor and explicit all-input scope.
- D03 I — zero-input stabilizer constructor and scope contrast lesson.
- D04 I — clean-ancilla constructor with explicit initialized-input assumptions.
- D05 I — named plan, bounded batch, duplicate names rejected, no hidden resource increase.
- D06 I — explain() meaningful status, domain, route, snapshot and obligation.
- D07 I — require() rejects FAIL, INCONCLUSIVE and UNSUPPORTED distinctly in text.
- D08 P — public type design, static checker and width-safe Pauli labels; wire-order tests.
- D09 P — typed local Pauli builders X/Z/Y(wire), tensor and signs without ambiguous label order.
- D10 P — rational sums ergonomic constructors and canonicalization.
- D11 P — clean-input equivalence/action and strict phase named forms.
- D12 P — separability cuts and Z branch probability/unnormalized expectation vocabulary.
- D13 P — noise and QEC vocabulary; code-only vs circuit-bound explicit.
- D14 P — structured result/error classes, machine-readable diagnostics, no bool ambiguity.
- D15 P — minimal counterexample explanation incl. basis axes and exact residual.
- D16 P — explicit composition and stage refinement with sound propagation of assumptions.
- D17 P — immutable plan and versioned, canonical JSON representation; safe schema validation.
- D18 P — pytest integration, strict CI policy with explicit unsupported/inconclusive behavior.
- D19 P — optional decorator syntax experiment; no implicit hardware run or hidden work.
- D20 P — execution bridge example: same immutable snapshot, verify before executing, reject mismatch.
- D21 P — compare current constructor vs named/fluent/decorator styles with users; choose one primary syntax, avoid redundant public DSLs.
- D22 P — API acceptance: all ten families, valid/invalid examples, typed API, understandable errors, no private imports.

### T — didactics and developer experience (P0/P1)
- T01 P — one command local install on each qualified OS; clean environment tutorial.
- T02 P — first proof with H, one Pauli, predicted outcome.
- T03 I — Bell correlations, deliberate phase mutation, all-input vs zero-input example.
- T04 P — ancilla leak example and clean uncomputation.
- T05 P — distinguish phase-insensitive equivalence and strict equality.
- T06 P — demonstrate non-Clifford limits, INCONCLUSIVE is not FAIL.
- T07 P — QEC code/error set and measurement instrument examples.
- T08 P — pytest + GitHub Actions minimal integration guide.
- T09 P — reference per contract: signature, equation, scope, resources, examples, limitations.
- T10 P — explanations: Pauli matrices, signed masks, conjugation, tableau, Q(sqrt2), exact vs numerical.
- T11 P — flow diagrams and notebook exercises: predict, run, inspect, modify, explain.
- T12 P — troubleshooting, error glossary, FAQ, migration from old API.
- T13 P — run every tutorial in CI from installed wheels; no stale notebooks.
- T14 P — documentation built under Diataxis (tutorial/how-to/reference/explanation).
- T15 P — first-contract target <10 min as study hypothesis, measure not assert.

### B — performance and research (all B1–B7)
- B101 E — cached inverse Clifford comparison, preserve raw samples and losses.
- B102 E — state comparisons vs StabilizerState and inverse (not dense only).
- B103 I — fix pauli-prop tuple and truncation handling; 30 near-Clifford cases.
- B104 P — add numerical preparation split vs prepared operator propagation; no numerical result promoted to exact.
- B201 I — batched exact Clifford state expectation prototype (48 cases, thresholds).
- B202 I — profile losing 2-wire/64-contract Python report workload.
- B203 P — integrate state route only after independent replay, full status/expectation parity and no budget borrowing.
- B204 P — optional compact diagnostic/verdict mode; never map INCONCLUSIVE to false property.
- B205 P — slots/validated immutable plans, eliminate duplicate hashing/admission, compare to A4.
- B206 P — packed batch and SIMD/lookup select only where measured useful.
- B207 P — micro/macro profiling (FFI, hashing, report, preparation, allocation), inspect negative cases.
- B208 P — paired held-out comparisons and regression gate.
- B301 P — T-count 0/4/8/12/16/24/32, depth, support size, topology and T density.
- B302 P — Aer MPS, stabilizer, extended stabilizer and statevector comparisons at matched accuracy.
- B303 P — disconnected factorization, low entanglement, high entanglement, graph/brickwork/Ising.
- B304 P — term growth, cone reduction, cancellation, block-Clifford aggregation, exact arithmetic limits.
- B305 P — >64 multiword representation feasibility; only Alpha blocker if declared support demands it.
- B306 P — coverage/time/memory curves, timeout and inconclusive counts.
- B401 P — GHZ/BV/Deutsch-Jozsa, phase kickback, QFT Clifford+T subsets, arithmetic/uncomputation.
- B402 P — QCEC equivalence with semantic mutants, equal rewrites, phase changes, dense small oracle.
- B403 P — use public held-out MQT/real Qiskit circuits within admitted alphabet; provenance and license.
- B404 P — transpile before/after, preserve strict phase decision; no silent approximate transpilation.
- B405 P — mutation operators: wrong wire/gate/sign/control, dropped entangler, missing uncompute; label equivalent mutants.
- B406 P — record sensitivity, false positives, inconclusive rate and coverage; no false verdict in corpus.
- B501 P — exact rational Pauli sums vs dense operator.
- B502 P — finite Pauli mixtures vs matching density-channel model; no general CPTP claim.
- B503 P — Z measurement branches, branch probability and unnormalized expectations, zero-probability cases.
- B504 P — stabilizer code commutation/independence and recovery table, repetition/Steane examples.
- B505 P — partial replay limitations per domain; compare independent algorithms when available.
- B601 P — benchmark manifest seeds, versions, source SHA, CPU/threads/affinity, host isolation.
- B602 P — fixed dedicated CPU, repeated fresh processes, warm/cold, p50/p95 and confidence intervals.
- B603 P — peak RSS and logical budget accounting; actual subprocess timeout/memory limits.
- B604 P — matched outputs and comparable setup, record negative results, held-out seeds.
- B605 X — independent replication on controlled hardware (requires access); shared CI not certification.
- B701 P — design external evaluation against pytest/Qiskit, tasks and consent protocol.
- B702 P — usability tasks: first contract, diagnose mutation, ancilla, integrate CI; compare syntax options.
- B703 P — record completion, time, errors, perceived ease, learning, not only satisfaction.
- B704 X — recruit 5–10 external developers and two reviewers; no invented participants or results.
- B705 P — anonymized evidence, publish limitations and changes; adoption is not guaranteed.
- B706 P — scientific contribution matrix against QBricks/QbC/Hoare/Stim/QCEC/QuCheck and related work.

### C — CI and test consolidation (P0)
- C01 E — inspect 32 research-related workflows in candidate; 31 broad/narrow research and alpha entries.
- C02 E — repeated broad path triggers and repeated native builds identified.
- C03 P — inventory test entrypoint, domain, oracle, fixture, mutation, platform, dependency and runtime.
- C04 P — map coverage to replacement tests; exact independent oracles and negative controls mandatory.
- C05 P — retain legacy SDK regression and native dependency audit required checks.
- C06 P — build once per OS/ABI/commit; reuse verified artifacts, not cross-commit binaries.
- C07 P — group short core tests; parallelize independent expensive suites; measure queue vs execution.
- C08 P — PR fast gate: admission, exact math, witnesses, replay, FFI, public smoke, typing, examples, dependency audit.
- C09 P — research extended gate: historical R5–R32 corpus, differential/metamorphic, resource/security and algorithms.
- C10 P — performance separate workflow; manual/controlled trigger, not unconditional on docs changes.
- C11 P — nightly/release full historical regressions and reproducibility; keep old evidence.
- C12 P — branch protection inventory and stable required check names before narrowing filters.
- C13 P — explicit always-run aggregator; skip optional jobs with documented dependency mapping.
- C14 P — concurrency per workflow/ref for superseded commits only; never cancel a final candidate blindly.
- C15 P — pin actions/dependencies and read-only permissions; no publishing credentials in tests.
- C16 P — compare old/new exact-head test IDs, verdicts, failure injection, time and compute; no weaker coverage.
- C17 P — only then disable redundant automatic triggers, archive scripts and remove unreachable runtime modules.
- C18 P — no blanket deletion, no removal of unique mathematical or security coverage, preserve rollback.
- C19 P — target: >=50% fewer redundant builds and >=30% PR wall time reduction; measure actual results.
- C20 P — release gate includes all required checks and slow-suite exact head, regardless of fast CI outcome.

### M — math, security, evidence and portability (P0/P1)
- M01 P — exact semantic specification for each domain, proof sketches, assumptions.
- M02 P — independent replay for newly optimized state route and mixed requests.
- M03 P — witness verification and adversarial tampering, canonical IDs and scope binding.
- M04 P — distinguish invalid evidence, unsupported replay and insufficient budget.
- M05 P — domain admission and strict builtin validation, bounded resource extraction.
- M06 P — no arbitrary Python sandbox claim; inspect custom gate normalization and concurrency.
- M07 P — differential/property-based fuzz, shrink counterexamples, persist regression fixtures.
- M08 P — memory, time, coefficient growth and logical budget audit; no false precision.
- M09 P — dependency vulnerabilities, SBOM/NOTICE, build provenance and legal review.
- M10 P — portable Linux/macOS/Windows artifact matrix; test oldest declared targets; Python/ARM scope explicit.
- M11 P — deterministic pure Python wheel cross-host, native reproducibility per target and independent builds.
- M12 P — reproducible docs, API stubs, sdist/wheel and packaging from clean checkout.
- M13 P — contribution guide, license, security reporting, scope/limitations and changelog.
- M14 P — signed/tagged local Alpha candidate only after owner approval; no public registry reservation.

## Parallel execution and exit

Parallel streams: integration/CI (A,C,M), contract experience (D,T),
performance (B1–B6), external validation (B7). Dependencies: A02 before
A03/A04; B1 results before B2 adoption; C03/04/12/16 before any CI
retirement; D21 before API freeze; B6 controlled and B7 external work
may be explicitly deferred as research if Alpha clearly labeled.
Math, admission, dependency, installation and public usability gates
cannot be waived to meet a schedule.

Alpha exit: exact-head required CI green, reproducible qualified local
packages; 10 domain families with clear limitations and named contracts;
tutorials run from wheels; no false verdict in held-out corpus, unsupported
and inconclusive tracked; comparative results including losses; source
and evidence reproducible; dependency/notice review; coherent version and
changelog; owner signoff. No claims of general speed superiority, formal
verification of all programs, novel science, or validated external adoption.
