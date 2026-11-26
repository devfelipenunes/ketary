# Quantum software engineering — production qualification

Status: internal pre-alpha. The product direction is mathematical modeling,
controlled experiments, verification, diagnosis, and reliable quantum software
engineering. Code concision and runtime overhead are quality attributes, not
the product's primary promise. Qiskit remains authoritative; no backend
replacement or hardware execution is implied.

## Production gates (not completed by writing this document)

| ID | Domain | Required exit evidence | Existing work |
| --- | --- | --- | --- |
| PROD01 | Mathematical specification | definitions, units, ordering, tolerance, domain, error/resource bounds for each numerical API; independent analytic/dense oracles | #254 #311 #249 |
| PROD02 | Verification | property/metamorphic tests, mutant detection, negative sentinels, replay and diagnosis scope; no false PASS on supported sentinel corpus | #257 #312 #316–322 |
| PROD03 | Numerical robustness | finite/near-singular input, cancellation, phase and derivative cases, precision budgets; documented failure rather than silent approximation | #273 #283–285 #306 |
| PROD04 | Workflows | end-to-end optimization, physics, protocols, variational and program verification; native comparisons plus independent reference outcomes | #255 #291–298 |
| PROD05 | Runtime and scalability | paired equivalent workload p50/p95 and isolated peak RSS on dedicated host; deterministic budgets, no unexplained regression | #256 #300–310 |
| PROD06 | API and compatibility | contract/stub parity, stable candidate surface, changelog and migrations; explicit supported OS/Python/dependency matrix | #208 #210 #230 |
| PROD07 | Reliability and security | core/dynamic/external isolation, malformed artifact/fault tests, dependency scans, provenance and reviewed licenses | #250 #277 #322 |
| PROD08 | Distribution and operations | clean wheel/sdist installation; exact-head and main CI; build hashes, dependency locks and reproducible procedure; signed release strategy reviewed separately | #230 #258 |
| PROD09 | Independent adoption | external developers/researchers complete real tasks, report errors and trust; separate blinded agent evaluation where useful | #211 #251 |
| PROD10 | Release governance | documented remaining limitations, manual technical review, name/license review, owner-approved release candidate and version; no automatic publication | #230 #258 |

Proposed quantitative gates, subject to owner review: 100% of supported
numerical public contracts linked to at least one positive and negative
oracle; >=95% combined statement/branch coverage without gaming; critical
semantic mutant kill rate 100% on declared finite sentinel set; no
unexplained warning, skip, critical known dependency vulnerability or
unresolved correctness bug in supported scope. These are engineering goals,
not attained metrics. Coverage and finite tests do not prove correctness.
Set per-workload runtime/memory thresholds after dedicated baseline.
Platform claims are restricted to tested configurations.

## Evidence baseline

PR #346 head 6994dad0: 1737 passed, 27 skipped, 37 pytest warnings,
95% combined coverage, 17/17 workflows passed; merge 27d84fd1 tree
identical. Post-merge push CI must be checked separately.
The 27 core skips all correspond to optional Aer; dynamic workflow was
successful, do not delete skips or require Aer in core. Warnings: 36 SciPy
SparseEfficiencyWarning instances in reference workflows; one Qiskit
RuntimeWarning in intentionally invalid coefficient fixture. Node action
deprecations are separate from pytest counts. Keep warnings visible,
review upstream and fix at the origin where possible.

## Independent mathematical assurance

Use deterministic seeded property tests and dense NumPy reference matrices
constructed from the Pauli definitions, not native Qiskit operator
conversion. Include non-real amplitudes, Y phases, permuted wire subsets,
strict global phase, noncommuting rejection, shared parameter derivatives
and deliberate semantic mutants. These are bounded small-system oracles,
not a new runtime, proof or scaling benchmark. See
tests/test_production_math_oracles.py. Record exact revision, JUnit output,
raw pytest warning/skip records and environment. Never silently expand
resource caps to make tests pass.

Independent human validation, controlled host results, formal verification,
hardware support and public distribution are not implied by this work.
No tag or publication until separate explicit approval.

## 2026-11-26 integrated functional evidence

#351 main 5c0d3798, exact head 36caaee8, 18/18 workflows, identical tree; 2039 core passed / 29 skipped / 38 warnings / 93% combined coverage; 2079 dynamic passed / 38 warnings / 94%. 51 authored comparison cases pass, covering 35/37 distinct selected tasks via direct or explicit native routes, not API-wide compatibility. Native metadata/barrier preservation remains unresolved. Core skips include optional Aer. New GenericBackendV2 warning reflects BasicSimulator fallback without Aer in core; no physical hardware validation. Production gates remain partial: dedicated hardware benchmark, independent user pilot, platform compatibility, mutation score and release/license review outstanding. CI connector filters to PR runs; push CI not confirmed.
