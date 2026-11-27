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

| ID | Epic / deliverable | Status at round 16 baseline | Exit gate |
|---|---|---|---|
| M01 | Semantic taxonomy and algebra | V | Exact/numeric/empirical separation; independent review |
| M02 | Signed Pauli transition and invariant | V | Dense oracle and exact replay |
| M03 | Joint clean subspace | V | All-input compression, clean witness |
| M04 | Full unitary equivalence modulo phase | V | All generators; phase and control caveats |
| M05 | Logical coherent action | V | Independent isometry and input-domain witness |
| M06 | Monomial action and relative phase | V | Exact CCX recognition, union partition, cap and witness |
| M07 | Sequential transition composition | V | Matching intermediate predicates; no invalid failure inference |
| M08 | Effect inequality and sequential CPTP | V | Numeric guard, forward replay and scope |
| M09 | Exact rational Pauli channel transitions | E | Exact coefficients and independent dense/analytic controls |
| M10 | General Hermitian predicates / sums | P | Exact supported coefficient algebra, explicit unsupported |
| M11 | Entanglement and separability contracts | P | Typed sufficient vs necessary witness scopes |
| M12 | Measurement, reset, classical branches | P | CP-TNI / total vs partial correctness, explicit approved scope |
| M13 | Strict and relative phase semantics | P | Phase-sensitive operations; no unsafe coherent-control reuse |
| M14 | Component contracts for arithmetic | V | Independent permutation, carry/phase/leak mutants |
| M15 | Recovery and syndrome contracts | V | Fixed X/Z patterns; arbitrary logical input, no fault tolerance claim |
| M16 | General error-correcting codes | P | Stabilizer logical generators, independent syndrome and logical oracle |
| M17 | Channel composition error bounds | P | Analytic additive bounds, numeric vs exact separated |
| M18 | Observable-native research syntax | E | Use existing q.X/Y/Z and @, ± single Pauli only |
| M19 | Unified experimental contract facade | E | Explicit route/domain, immutable spec, compatible report semantics |
| M20 | Reusable component registry design | P | Explicit IDs, domain and composition, no global mutable registry |
| M21 | Contract implication/reuse | P | Verified rule set; counterexamples and invalid substitution |
| M22 | Diagnostics and explanations | P | Failed generator, basis/phase evidence, bounded replay |
| M23 | Versioned evidence records | E | Strict serialization, request/engine fingerprint and replay/tamper controls |
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
