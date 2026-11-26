# Twenty-front production qualification ledger

The owner prioritizes PROD11–30. Existing PROD01–10 gates and #348/#352
remain authoritative. This ledger maps work and blockers; no percentage of
production readiness is inferred.

| Front | Existing evidence / candidate | Exit criteria and remaining work |
| --- | --- | --- |
| PROD11 coverage | #371 exact combined coverage gate integrated; #374 96.543738% Core / 96.561554% Dynamic | >=95% combined without weakening; fault/negative tests |
| PROD12 mutation | #370 integrated; #372 100/100 declared mutants, zero invalid/surviving | 100 critical declared mutants with isolated baseline and no invalid kills |
| PROD13 fuzz | #366 1000 seeded cases integrated, both suites pass | >=1000 distinct generated cases; replay/minimization/adversarial inputs |
| PROD14 numerics | #359 compensated Pauli aggregation; #366 generated | cancellation, near-singular PSD, tolerance and propagation |
| PROD15 programs | 35/37 selected routes; #360/#369/#374 42 fixture rows, not globally deduplicated | 100 executable distinct programs; independent oracles; no prompt count as completed |
| PROD16 complex algebra | #355 complex expectation, #359 stable aggregation | finite complex algebra, product/adjoint/expectation consistency |
| PROD17 Hessian | #363 exact-in-model bounded public Hessian | multi-occurrence exact/approx derivation, conditioning, budget; API review |
| PROD18 QGT | #362 bounded public QGT, gauge and shared parameters | multi-qubit/shared-parameter analytic checks and rank/singular cases |
| PROD19 channels | #364 local ordered CPTP and native composition | channel composition, local mapping, positivity/trace tests, resource caps |
| PROD20 approximation | 36 two-term cases; #372 192 multi-term comparisons integrated | general error bounds, explicit norm, tolerance and counterexample |
| PROD21 dynamic | #361 nested 3 levels and 1024-node cap | nested control decision, measurement provenance, resource/shot semantics |
| PROD22 diagnosis | existing contracts/reports; #373 restart minimization integrated | structured incompatibility and native failure recovery, no false PASS |
| PROD23 metadata/barriers | #368 explicit projection/native snapshot integrated; strict import rejects | explicit preservation contract, serialization and transformation rules |
| PROD24 synthesis | <=5-wire dense verified; #369 bounded Hamiltonian fallback | width/depth scaling, native cost profile and strict operator scope |
| PROD25 performance | CI paired timings/RSS | authorized dedicated host, pinned environment, raw p50/p95 and RSS |
| PROD26 security | dependency scans, isolation, artifact checks | manual upstream notices/license, fault injection, threat model |
| PROD27 platforms | #365 full three-OS previous candidate passed; final exact candidate pending | full per-platform wheel/source/dynamic validation, documented versions |
| PROD28 docs | resource, API lifecycle and math guides | complete public formula and example inventory, migration/limitations |
| PROD29 usability | 30 prompt-only tasks and crossover protocol | independent participants and separate agent runs, recorded results |
| PROD30 release | clean wheel/sdist checks | reproducibility, exact main CI, review, legal/name clearance, owner approval |

No hardware execution, new simulator, package rename or publication.

## Evidence snapshot — 2026-11-26

Main 6f1e8a8bbd25882fbdfaa4dc8d7152891dc0450b matches tested #374 head
9d51aa9dda5aac2f89ad695b74b68007cc480531 (zero changed files after merge).
[Validate](https://github.com/devfelipenunes/ketary/actions/runs/45828925745):
3755 Core passed / 47 optional-Aer skips; 3813 Dynamic passed; 38 warnings
in each; 20/20 triggered workflows passed. Exact combined coverage as above.
[Earlier integrated mutation evidence](https://github.com/devfelipenunes/ketary/actions/runs/45828543580).
Push CI not independently confirmed. These are revision-scoped observations,
not release approval. See [capability matrix](capability-matrix.md).
