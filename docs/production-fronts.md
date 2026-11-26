# Twenty-front production qualification ledger

The owner prioritizes PROD11–30. Existing PROD01–10 gates and #348/#352
remain authoritative. This ledger maps work and blockers; no percentage of
production readiness is inferred.

| Front | Existing evidence / candidate | Exit criteria and remaining work |
| --- | --- | --- |
| PROD11 coverage | #353 93% core/94% dynamic | >=95% combined without weakening; fault/negative tests |
| PROD12 mutation | #354 8/8 declared mutants | 100 critical declared mutants with isolated baseline and no invalid kills |
| PROD13 fuzz | 205 previous oracles; 60 new seeded reversible cases | >=1000 distinct generated cases; replay/minimization/adversarial inputs |
| PROD14 numerics | strict phase, independent complex and dense oracles | cancellation, near-singular PSD, tolerance and propagation |
| PROD15 programs | 35/37 selected task solutions, 30 new prompts | 100 executable distinct programs; independent oracles; no prompt count as completed |
| PROD16 complex algebra | #355 complex native expectation candidate | finite complex algebra, product/adjoint/expectation consistency |
| PROD17 Hessian | 18 research differential cases | multi-occurrence exact/approx derivation, conditioning, budget; API review |
| PROD18 QGT | 18 research cases, gauge invariance | multi-qubit/shared-parameter analytic checks and rank/singular cases |
| PROD19 channels | #355 CPTP Kraus candidate | channel composition, local mapping, positivity/trace tests, resource caps |
| PROD20 approximation | 36 two-term Lie/Strang cases | general error bounds, explicit norm, tolerance and counterexample |
| PROD21 dynamic | #351/#353 import and expanded preflight | nested control decision, measurement provenance, resource/shot semantics |
| PROD22 diagnosis | existing contracts and reports | structured incompatibility and native failure recovery, no false PASS |
| PROD23 metadata/barriers | direct import deliberately rejects | explicit preservation contract, serialization and transformation rules |
| PROD24 synthesis | <=5-wire dense verified | width/depth scaling, native cost profile and strict operator scope |
| PROD25 performance | CI paired timings/RSS | authorized dedicated host, pinned environment, raw p50/p95 and RSS |
| PROD26 security | dependency scans, isolation, artifact checks | manual upstream notices/license, fault injection, threat model |
| PROD27 platforms | new candidate smoke matrix | full per-platform wheel/source/dynamic validation, documented versions |
| PROD28 docs | resource, API lifecycle and math guides | complete public formula and example inventory, migration/limitations |
| PROD29 usability | 30 prompt-only tasks and crossover protocol | independent participants and separate agent runs, recorded results |
| PROD30 release | clean wheel/sdist checks | reproducibility, exact main CI, review, legal/name clearance, owner approval |

No hardware execution, new simulator, package rename or publication.
