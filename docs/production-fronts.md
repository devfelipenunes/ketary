# Twenty-front production qualification ledger

The owner prioritizes PROD11–30. Existing PROD01–10 gates and #348/#352
remain authoritative. This ledger maps work and blockers; no percentage of
production readiness is inferred.

| Front | Existing evidence / candidate | Exit criteria and remaining work |
| --- | --- | --- |
| PROD11 coverage | #367 95% rounded core/dynamic; exact gate candidate | >=95% combined without weakening; fault/negative tests |
| PROD12 mutation | #367 38/38 strict JUnit, #370 72 declared candidate | 100 critical declared mutants with isolated baseline and no invalid kills |
| PROD13 fuzz | #366 1000 seeded cases integrated, both suites pass | >=1000 distinct generated cases; replay/minimization/adversarial inputs |
| PROD14 numerics | #359 compensated Pauli aggregation; #366 generated | cancellation, near-singular PSD, tolerance and propagation |
| PROD15 programs | 35/37 selected routes; #360 12 fixtures; #369 27 candidate | 100 executable distinct programs; independent oracles; no prompt count as completed |
| PROD16 complex algebra | #355 complex expectation, #359 stable aggregation | finite complex algebra, product/adjoint/expectation consistency |
| PROD17 Hessian | #363 exact-in-model bounded public Hessian | multi-occurrence exact/approx derivation, conditioning, budget; API review |
| PROD18 QGT | #362 bounded public QGT, gauge and shared parameters | multi-qubit/shared-parameter analytic checks and rank/singular cases |
| PROD19 channels | #364 local ordered CPTP and native composition | channel composition, local mapping, positivity/trace tests, resource caps |
| PROD20 approximation | 36 two-term Lie/Strang cases | general error bounds, explicit norm, tolerance and counterexample |
| PROD21 dynamic | #361 nested 3 levels and 1024-node cap | nested control decision, measurement provenance, resource/shot semantics |
| PROD22 diagnosis | existing contracts and reports | structured incompatibility and native failure recovery, no false PASS |
| PROD23 metadata/barriers | #368 explicit projection/native snapshot candidate; strict import rejects | explicit preservation contract, serialization and transformation rules |
| PROD24 synthesis | <=5-wire dense verified | width/depth scaling, native cost profile and strict operator scope |
| PROD25 performance | CI paired timings/RSS | authorized dedicated host, pinned environment, raw p50/p95 and RSS |
| PROD26 security | dependency scans, isolation, artifact checks | manual upstream notices/license, fault injection, threat model |
| PROD27 platforms | #365 full three-OS previous candidate passed; exact current candidate pending | full per-platform wheel/source/dynamic validation, documented versions |
| PROD28 docs | resource, API lifecycle and math guides | complete public formula and example inventory, migration/limitations |
| PROD29 usability | 30 prompt-only tasks and crossover protocol | independent participants and separate agent runs, recorded results |
| PROD30 release | clean wheel/sdist checks | reproducibility, exact main CI, review, legal/name clearance, owner approval |

No hardware execution, new simulator, package rename or publication.
