# Contract Engine — master qualification roadmap

Status: experimental research, PR #512. The existing public Contract checks
Result snapshots; do not change its meaning. One Ketary facade, Qiskit remains
authoritative for mutable circuits, Rust owns immutable bounded exact kernels.
No production release, generic simulator, new DSL, or public API approval.
This supersedes the research sequencing in contract-engine-lab.md, not the
canonical architecture or compatibility rules. Q01–Q10 are mapped below.

## Workstreams and exit criteria

Statuses: V = experiment validated in CI; E = experiment being validated;
P = pending qualification; B = external blocker. V is not release approval.

| ID | Epic / deliverable | Status at round 18 baseline | Exit gate |
|---|---|---|---|
| M01 | Semantic taxonomy and algebra | V | Exact/numeric/empirical separation; independent review |
| M02 | Signed Pauli transition and invariant | V | Dense oracle and exact replay |
| M03 | Joint clean subspace | V | All-input compression, clean witness |
| M04 | Full unitary equivalence modulo phase | V | All generators; phase and control caveats |
| M05 | Logical coherent action | V | Independent isometry and input-domain witness |
| M06 | Monomial action and relative phase | V | Exact CCX recognition, union partition, cap and witness |
| M07 | Sequential transition composition | V | Matching intermediate predicates; no invalid failure inference |
| M08 | Effect inequality and sequential CPTP | V | Numeric guard, forward replay and scope |
| M09 | Exact rational Pauli channel transitions | V | Exact coefficients and independent dense/analytic controls |
| M10 | General Hermitian predicates / sums | P | Exact supported coefficient algebra, explicit unsupported |
| M11 | Entanglement and separability contracts | P | Typed sufficient vs necessary witness scopes |
| M12 | Measurement, reset, classical branches | P | CP-TNI / total vs partial correctness, explicit approved scope |
| M13 | Strict and relative phase semantics | P | Phase-sensitive operations; no unsafe coherent-control reuse |
| M14 | Component contracts for arithmetic | V | Independent permutation, carry/phase/leak mutants |
| M15 | Recovery and syndrome contracts | V | Fixed X/Z patterns; arbitrary logical input, no fault tolerance claim |
| M16 | General error-correcting codes | P | Stabilizer logical generators, independent syndrome and logical oracle |
| M17 | Channel composition error bounds | P | Analytic additive bounds, numeric vs exact separated |
| M18 | Observable-native research syntax | V | Use existing q.X/Y/Z and @, ± single Pauli only |
| M19 | Unified experimental contract facade | V | Explicit route/domain, immutable spec, compatible report semantics |
| M20 | Reusable component registry design | P | Explicit IDs, domain and composition, no global mutable registry |
| M21 | Contract implication/reuse | P | Verified rule set; counterexamples and invalid substitution |
| M22 | Diagnostics and explanations | P | Failed generator, basis/phase evidence, bounded replay |
| M23 | Versioned evidence records | V | Strict serialization, request/engine fingerprint and replay/tamper controls |
| M24 | Independent evidence verification | P | Separate implementation; no claim of authenticity |
| M25 | Native immutable admission | V | Canonical bytes and explicit versioned identity |
| M26 | Sparse exact arithmetic and witness | V | Coefficient bounds, cap and dense oracle |
| M27 | Bit-slicing and native batch | V | Exact parity, same budget, compare Qiskit |
| M28 | Causal cones and inverse cancellation | V | Independent parity and capability |
| M29 | Native projection and compression | V | Replayed witness, matched scope |
| M30 | Unified planner and route provenance | P | Same semantics, retained attempted routes and caps |
| M31 | Native factorization of general Pauli transitions | P | Component sign and aggregate bounds, independent oracle |
| M32 | Resource ledger incl scans/witness/alloc | P | Explicit separate caps, overflow and rejection tests |
| M33 | Memory profiling / allocator highwater | P | Isolated RSS and allocation data, worst-case bounded input |
| M34 | SIMD, tableau, threading research | P | Adopt only demonstrated gains, no implicit workers |
| M35 | Stress and property-based fuzzing | P | Held-out seeds, budget boundary, malformed FFI |
| M36 | Matched algorithm corpus | V | Graph, GHZ, QAOA symmetry, arithmetic, recovery |
| M37 | Entangled/noncommuting held-out workloads | P | More active interacting data, independent control |
| M38 | External Qiskit/Stim/QCEC comparisons | P | Matched guarantee and setup, publish losses as well |
| M39 | Benchmark methodology and raw data | V | p50/p95, cold/warm, provenance; controlled host still needed |
| M40 | Dedicated CPU host #100 | B | Controlled environment, repeat, RSS and latency |
| M41 | Lab and dashboard | V | Executable native lab, raw data, honest snapshot |
| M42 | Cross-platform native wheels | V | CPython 3.12 Linux/Windows/macOS; full latest-head matrix |
| M43 | Portable wheel policy and reproducibility | P | Pinned toolchain, clean install, artifact reproducibility |
| M44 | Dependency/security and notices | P | RustSec, SBOM, third-party notices, review |
| M45 | Adversarial input / FFI audit | P | Reject unsupported and malformed before expensive work |
| M46 | Developer study packet #462 | B | Independent review of frozen tasks and scoring |
| M47 | Human usability #165 | B | Consenting real users; matched tasks, actual data |
| M48 | Documentation and teaching | P | Runnable examples for every supported scope, limitations |
| M49 | Public API proposal and migration | P | Explicit owner approval, ADR, stubs, inventory, regressions |
| M50 | Integration / candidate review | P | Exact-head CI, independent review, release gates; no publication |

## Execution waves (parallel within wave; dependencies are explicit)

- W1: M18/M19/M23 (facade and evidence), M09 (exact channels), M35
  (negative controls), review M01–M08 and M14–M15 results. No public changes.
- W2: M30–M32, M20–M22, M10/M13, M17, M37. Preserve validated semantics;
  resource ledger and independent oracles before expanding caps.
- W3: M11/M12/M16 after mathematical/owner scope review, M24/M33/M34/M38,
  M41/M43/M44/M45 and M48. No automatic selection or general simulator.
- W4: M40/M46/M47 when external prerequisites available; M49 after
  semantics/UX/review, M50 only after all mandatory gates.

Parallel validation: each implementation has its own job, fail-fast disabled.
Revalidate exact head, inspect raw artifacts and scope, record failures and
inconclusive separately; do not promote an optimization from noisy timings.
Do not close external issues merely because a protocol or CI suite exists.
No new public surface without approved RFC, compatibility and type review.


## Round 18 — parallel work queues (all 50 IDs)

Baseline PR #512 head 2e514539ca437462193124610246ad6c2999e25a:
17/17 PR-triggered workflows succeeded; master W1 forms, evidence and noise
jobs all succeeded. M09/M18/M19/M23 experimental status promoted to V only.
This baseline has 23 V, 24 nonblocked pending/partial and 3 external blockers.
R18 changes need their own exact-head CI. No publication or public API changes.

| Lane | IDs (each assigned once) | Immediate acceptance target |
|---|---|---|
| A1 semantics | M01–M10 | exact Hermitian sums, prior invariant regressions, dense oracle |
| A2 advanced | M11–M13, M16–M17 | entanglement certificate scope; measurement/reset and phase; general recovery and error bounds |
| B1 library | M14–M15, M20–M22 | component identity/domain; sound implication, constructive witness |
| B2 API/evidence | M18–M19, M23–M24 | facade regression, independent verification and tamper checks |
| C1 native | M25–M32 | immutable admission, exact arithmetic, route parity, factoring and bounded accounting |
| C2 native safety | M33–M35, M45 | isolated allocator, SIMD/thread experiments, held-out fuzz and FFI rejection |
| D1 comparisons | M36–M40 | matched guarantees on held-out workloads, external oracles, dedicated host when available |
| D2 distribution | M41–M44, M48 | lab records, repeatable wheels, SBOM/notice audit, runnable docs |
| D3 external | M46–M47 | frozen protocol, real independent reviewer and consenting participants |
| E integration | M49–M50 | compatibility ADR and candidate qualification, no release until approved |

These lanes are a scheduling plan, not a claim of ten live workers.
R18 implementations submitted in contracts18.py and front_master18.py:
- M10: rational Hermitian Pauli sums using the native exact propagator; no arbitrary Hermitian algebra.
- M12: exact adjoint rules for nonselective Z measurement and reset, not conditional branches.
- M13: independent bounded numerical strict unitary/controlled phase oracle; not exact strict proof.
- M16: independent commuting stabilizer generator admission and syndrome only; not general recovery.
- M17: exact composition of supplied CPTP diamond norm upper bounds, not certification of the input bounds.
- M24/M32/M35/M37: partial numerical oracle, accounting, negative controls and held-out small interacting cases; do not mark the full gates as complete.
M11 Bell-state entanglement certification, M20–M22, M30–M31 and remaining gates
are not implemented by this patch. M40/M46/M47 remain blocked.
Any result with a budget/cap exhaustion is inconclusive. The phase-insensitive
Rust circuit identity must not be used as a strict-phase evidence identity.


## Round 19 — planner, reusable components and independent replay

R18 #513 is still under CI; do not promote its partial gates yet. R19 stacks on its exact head 0c3959255560bff221a703924b4e2f273e64cfb5 so the preceding validation remains isolated.
- M20/M21: immutable Clifford component registry, recheck actual circuit bytes and both source guarantees before multiplying Hermitian conjugation identities; reject anticommuting products and changed snapshots.
- M22: native planner returns attempted route, status, circuit/obligation and a mathematical witness when definitive failure is found.
- M24: separate exact Clifford implementation using ordered X/Z generator multiplication with powers of i. It does not call Rust propagation. Still shares the documented gate alphabet and Python admission helpers; no complete serialized-evidence verifier or non-Clifford certificate.
- M30/M31: deterministic native direct/cone/component planner for signed Pauli transitions. Factoring uses disconnected interaction components and exact local Rust propagation. Local non-Pauli images remain inconclusive.
- M32: disjoint conservative logical budget reservations, including estimated merge/witness work. Not a time, memory or full admission cap.
- M35/M37/M39: held-out seeds, matrix/witness parity, invalid substitution and budget tests; raw timings are shared-runner pilot measurements only.
- Three matrix CI jobs: independent, planner, library. Status remains experimental until exact-head results are inspected.

R19 does not implement M11 entanglement, M33/M34 native allocator/SIMD experiments, M38 external full comparison, M43/M44 distribution/security, or M49/M50 public integration. External M40/M46/M47 still blocked. No production change or publication.
