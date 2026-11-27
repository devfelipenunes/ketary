# QContract CI consolidation — migration decision record

## Observed baseline
The successful B1–B5 run 46080608088 at 3e4487b2 produced a read-only
CI inventory (artifact 15237416418): 32 research workflow files,
31 broad research triggers, 24 with explicit maturin build commands.
These are static file counts, not actual runner counts.
The shared-build pilot passed one build plus eight consumers (9/9
jobs); each consumer verified commit and hashes of the shared wheels.
Compared with a design of eight separate builds, this removes seven
builds in this lab (87.5% fewer); no measured wall-time reduction claim.

## Candidate mapping, not retirement approval
| Historical workflow groups | Existing coverage | Proposed destination |
|---|---|---|
| native-contract-engine, contract-engine-validation | mathematical/negative controls, native tests, kernel benchmark | Fast math + Extended; benchmark in Performance |
| round5/6/7/8 | experimental strategies and legacy C/C++/ctypes experiments | Extended history; check unique fixture coverage before archive |
| contract-engine-lab, pyo3, consolidated, qiskit | syntax, real SDK adapter, batch, snapshots, direct comparison | Fast installed package + Extended old API |
| qualification, optimized, roadmap, specialized, master, round18 | projection, arithmetic, phase, logical/clean action, noise, code, evidence | Extended domain matrix; Fast smoke for every family |
| round19–24 | independent evaluator, planner, DAG, external comparisons, certificates, prepared tableau, profiling, witnesses | Extended correctness + Performance; replay/tamper in Fast |
| round25–29 | binary, weighted DAG, SIMD, exact semantics, resources, spatial, FFI, fuzz | Extended independent/negative tests; selected FFI/replay in Fast |
| round30–32 | integrated domains, budget, platform, notice, reproducibility, native lookup and comparisons | Extended and Release; preserve native binary checks |
| native-dependency-audit | native supply-chain checks | retain required check until equivalent replacement approved |
| qcontract-alpha | isolated wheels, smoke, typing, reports, distribution | retain qualification; reuse artifact per OS/ABI |
| Validate experimental SDK (outside 32-file inventory) | legacy SDK regression | retain while old SDK exists |

Every old workflow and test remains intact. Candidate next step is
enumerating executable test IDs and oracle/fixture identities, collecting
exact-head results from both pipelines, introducing intentionally broken
controls, then comparing coverage and actual wall time. No required
check name changes without checking repository protection. The cancelled
R30 macos-14 job has a distinct historical runner; R31 macos-15 and the
A4 installed macOS check are green at the same head, but the cancelled
check itself is not a passing test. Do not override required checks.

## Runtime architecture
A4 Linux installed wheel static AST audit: 32 core modules, 2669 source
lines, 115 local-import edges; all 32 syntactically reachable from six
API roots. Two deferred imports of the historical SDK remain in native9
and facade17. This is not dynamic reachability; do not remove modules
on this evidence. The candidate runs runtime_audit.py on each built
wheel. Next separate canonical src/qcontract, adapter, kernel and lab
directories with per-module parity. Historical source and evidence
remain available; do not silently copy or maintain divergent algorithms.

Proposed future pipeline:
1. Build once per exact commit/target/ABI, audit SHA-256, RECORD and license.
2. Fast checks consume these wheels: public API, exact mathematical
   negative controls, admission, FFI, replay, smoke, examples, typing.
3. Extended checks reuse artifacts and independently exercise all
   historical unique domains/fixtures; dependency versions and legacy
   ABI needs may require separate builds.
4. Performance on isolated jobs without mandatory shared-host timing
   thresholds. Release gate full exact-head extended plus native
   reproducibility, dependency and artifact checks.
5. Move triggers only after mapping and coverage parity, preserve
   manual/nightly full suite, verify required checks and rollback.

No old automatic trigger has been disabled in this candidate. No new
claim of 50% overall build or 30% PR duration savings until measurement.
