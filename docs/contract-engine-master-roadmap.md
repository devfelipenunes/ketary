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


## Round 20 — independent exact oracle and mathematical contracts

R18 17/17 workflows succeeded. R19 17/18 workflows succeeded (SDK general
regression in progress at inspection); R19 specialist matrix 3/3 passed.
Seven original R18/R19 lab.json reports and commit.txt files were inspected:
2550 reported checks total. Planner median 0.011371/0.014837/0.570375 ms
for 16/32/64 wires, respectively; only the 64-wire example required all three
routes. These are shared-host, disconnected-component pilot results, not
general speedups or resource qualification.

R20 implements:
- M24: second exact Clifford+T oracle using all computational basis columns
  with integer coefficients in Z[1/sqrt(2),i]. Bounded to 5 wires, 512 gates.
  Compares U A=B U, returns exact mismatch coordinates. Does not consume
  serialized evidence, establish authenticity or verify strict source phase.
- M11: exact Phi+ Bell pair target on zero input, using XX/ZZ stabilization.
  Failure is not a separability witness; no arbitrary entanglement decision.
- M16: Knill-Laflamme finite Pauli error set criterion for independent
  commuting stabilizers. A pass proves existence of recovery, not an actual
  recovery circuit, hardware threshold or fault tolerance.
- M35/M37/M38/M39: held-out mixed Clifford+T and dense Qiskit cross-checks,
  GHZ and Bell phase/bit mutants, 3/5/7-qubit code projector comparisons;
  exact column oracle and native planner timing comparison. These are new
  proposed tests, not results until CI passes.

References: Knill and Laflamme, Phys. Rev. A 55, 900 (1997),
https://doi.org/10.1103/PhysRevA.55.900 ; Giles and Selinger, Phys. Rev. A
87, 032332 (2013), https://doi.org/10.1103/PhysRevA.87.032332 .
For future M38, MQT QCEC documents DD, simulation and ZX methods:
https://mqt.readthedocs.io/projects/qcec/en/stable/equivalence_checking.html .
Compare only equivalent obligations (e.g. U A=B U) and explicit phase scope.

Next unresolved research: scalable independent non-Clifford certificates;
connected factorization/cut decomposition; planner preselection and
allocation accounting; measured native profiling; reproducible wheels,
security and FFI audit; matched external benchmarks and actual recovery
circuits. External M40/M46/M47 remain blocked. No public API change.


## Round 21 — integrated research pilots

R18 and R19 CI complete (17/17 and 18/18). R20 specialized jobs 3/3
completed; overall 18/19 at inspection. R21 is stacked on R20 exact head.
Seven fail-fast-disabled suites submitted, not validated yet.

| Research lane | Executable deliverable | Remaining gate |
|---|---|---|
| Connected factorization M31 | Temporal Pauli cuts on connected chains, local exact replay | Arbitrary spatial cuts and non-Pauli boundary contractions |
| Adaptive planner M30/M32 | Cone preselection and baseline comparison | Learned/cost-driven route ordering, complete resource accounting |
| Native tableau M27/M34 | Compare existing native bit slicing and scalar, concurrent threads | New SIMD implementation, persistent native tableau |
| Decision diagrams M29/M31 | Exact hash-consed amplitude DAG roundtrip and node counts | Weighted DD operations, direct gate evaluation, scalable admission |
| Exact arithmetic M10/M26 | Common power-of-two normalization, exact reconstruction | Native coefficient normalization and bit-complexity budget |
| Certificates M23/M24 | Request-bound segmented independent exact replay; tamper controls | Portable serialized certificates, independent large non-Clifford checker |
| Hierarchy M20/M21 | Local Pauli transition composition on connected circuits | General contract algebra and nested non-Pauli domains |
| Algorithms M36/M37 | QFT/Grover/QPE/QAOA/VQE analytic numerical reference fixtures | Ketary-native contract lowering for arbitrary rotations |
| Native profiling M33/M34 | Scalar/bitslice/threaded timings, Python peak and process RSS | Isolated native allocations, SIMD, dedicated host |
| Recovery M16 | Syndrome-to-Pauli table and all-logical-state dense validation | Physical extraction and fault-tolerant recovery |
| Security M35/M44/M45 | FFI malformed-input probes, dependency inventory | Full fuzz, SBOM format and vulnerability audit |
| External M38 | Stim/Qiskit signed Clifford image and QCEC modulo-phase pilot | Full matched benchmarks including setup and controlled host |
| Distribution M43/M44 | Two clean target builds, SHA256 comparison and cargo/pip inventory | Cross-host reproducibility, signed SBOM, vulnerability review |

R21 is an experimental implementation increment, not completion of these
lanes. The adaptive route has separate reduced-snapshot provenance; its
budget is abstract logical work, not memory/time. The DAG only compresses
an already constructed bounded vector. External comparisons isolate
pinned stim 1.16.0 and mqt.qcec 3.8.0 in one job, not SDK dependencies.
QCEC probable equivalence/timeout is not a proof. No publication/merge.
M40/M46/M47 remain external blockers.


## Round 22 — persistent Rust tableau and direct decision DAG

R21 exact head d752fec290f99eebe2eb405f49c210455cdc2524: 20/20
workflows, 7/7 specialized suites. Reopened original lab.json reports:
Stim prepared queries 1.342–3.534 us vs Rust gate scans 5.880–7.355 us
(256 gates, 4–64 wires). Native bit-slicing 3.9–10.0x faster than scalar
for 64 transitions; Python thread overhead worsened latency. Temporal cuts
verified structured connected 64-wire / 384-gate case; same-host wheels
byte-identical. These observations do not establish general superiority.

R22 prototypes (pending CI):
- M27/M30/M34: immutable Rust inverse Clifford tableau built from 2n generator
  images using existing bit-slicing; exact signed Pauli multiplication with
  popcount, sparse set-bit traversal, query independent of gate count.
  Separate build and query logical budgets. No implicit public dispatch.
- M34: bounded native scoped threads for up to 4096 queries, 1–8 workers.
  Thread creation included in timing; no claim of speedup or SIMD.
- M38/M39: match prebuilt query scope with Stim and Qiskit at 4/16/32/64 wires,
  256/4096 gates; report setup separately, single and 64-query latency;
  library output representations differ. Shared runner, not controlled host.
- M29/M31: direct exact unweighted amplitude DAG gates H/S/Sdg/X/Z/CX/T/Tdg,
  hash-consed nodes and memoized subgraph operations, no dense expansion
  inside backend. Bounded 20 wires/512 gates, historical arena cap and logical
  work; not a weighted DD, arbitrary rotation engine, native allocation cap
  or general efficient simulator. Compare exact columns at 2–5 wires;
  structured uniform, GHZ and T-phase fixtures at 8–20 wires.
- M35/M45: malformed/budget admission and bit 63 controls; exact parity
  against separate algebra, previous kernel, Stim and Qiskit.

Four matrix suites exact/external/parallel/dag. No merge or production
promotion. Explicit SIMD, native allocation accounting, persistent worker
pool, weighted DD, cut decomposition and physical syndrome extraction
remain open, as do M40/M46/M47 and public integration gates.


## Round 23 — prepared reports, portable evidence and DAG state contracts

R22 exact head 54c723c0ae8f1cf72a1d384561a17fa011cc1173: all four
specialist jobs passed; overall 20/22 workflows succeeded at inspection
(SDK and native dependency audit pending). Original four lab.json and
commit.txt reports inspected. Exact tableau 5001 checks, external 512,
DAG 110. Prepared single-query medians 0.547–1.033 us vs Stim
2.017–4.923 us on eight shared-host scenarios. At 64 wires / 4096 gates:
Rust setup 104.451 us, Stim setup 899.152 us; single 1.033 vs 4.923 us;
64-query batch 37.586 vs Stim Python loop 231.674 us. Different output
representations and native batching vs Python loop limit interpretation.
Native scoped threads lose on most small batches; 64 wires/4096 queries
1.376065 ms serial vs 1.153330 ms with four threads (pilot). No automatic
threading recommendation. Direct DAG 20-wire uniform/GHZ/phase live
nodes 21/59/140, historical arena 462/291/1967, simulation medians
0.809066/0.455283/3.473005 ms; structured fixtures only.

R23 adds three pending suites:
- M19/M22/M27/M30: private prepared tableau dispatch with request-bound
  reports and exact failure witnesses, logical budget admission, fallback
  to old planner. Does not alter public APIs or enable native concurrency
  automatically (max 64 contract reports in this adapter).
- M23/M24/M35: canonical bounded JSON serialization of temporal Pauli
  certificates, strict integer schema, duplicate rejection, original
  snapshot binding and independent local replay. Hash is not signature;
  forged digest with altered mathematical obligations is tested.
- M02/M11/M29/M37: exact Pauli expectation via memoized DAG contraction
  without materializing amplitudes; normalized zero-input pure-state
  eigencontracts. Not arbitrary state or operator equivalence, no weighted
  diagrams. Test dense oracle agreement and GHZ through 20 wires.

No merge/public release. Physical recovery, weighted DD, native memory,
SIMD, scalable cut decomposition, independent external review and
dedicated-host qualification remain open.
