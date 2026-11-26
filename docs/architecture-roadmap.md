# Architecture progression and scalability

The architecture is an in-process scientific SDK with one facade and a
native authoritative model. This roadmap is incremental; architectural
purity is not a goal by itself. Pre-alpha is not a production guarantee.

## Progression and exit gates

| Stage | Scope | Exit evidence |
|---|---|---|
| ARCH01 | Architecture, module ownership and ADRs | C4-inspired views; dependency and optional-import tests (#42) |
| ARCH02 | Consolidate duplicated native execution paths | Private ideal execution boundary, unchanged signatures, shared monotonic trace cursor; native prefix/complex state and budget tests |
| ARCH03 | Protect dependency direction | Eager import cycle guard; foundation/import restrictions; optional integrations isolated; documented local back-references |
| ARCH04 | Review internal change pressure | Assess Circuit/Result responsibility, duplicated logic and change history; extract only a coherent private unit with oracles |
| ARCH05 | Measure scaling and preserve costs | Matched diagnostic benchmarks, resource preflight, raw timings/RSS; controlled host pending |
| ARCH06 | Stabilize extension policy | Criteria for new APIs, algorithms, integrations; exact-head CI, review and merged tree; no public release |
| ARCH07 | Future portability decision | Only when a real second target requires it: approved ADR, compatibility matrix, PoC and equivalent benchmarks |

ARCH01 implemented in #42. ARCH02/03 and ARCH06 policy integrated in #43.
See the [architecture audit](architecture-audit-2026-11-26.md) for observed
coupling, resource and API scaling risks and prioritized next steps. ARCH04 is a conditional maintenance review, not a mandate to split
files by size. ARCH05 existing diagnostic suite remains required; controlled
dedicated-host data and human evaluation are outstanding. ARCH07 is deferred,
not a commitment to add a backend.

## Scalability model

| Work | Dominant payload / growth | Current strategy |
|---|---|---|
| Ideal dense state | 16 * 2^n bytes (complex128) | Explicit run budget, defensive result |
| Dense operator | 16 * 4^n bytes per matrix | Width <=8, two/three-matrix checks |
| Full trace | (g+1) state snapshots | Explicit bounded trace |
| Aligned checkpoint comparison | Current states, not full history | Monotonic cursor; historical conservative budgets retained |
| Sweeps | Up to 32 results plus working payload | Bound zipped plan; aggregate guard |
| Query plan | One state + selected density output | One simulation, explicit payload estimate |
| Weighted Pauli variance | Dense small operator or streamed state-sized work | User-visible bounded paths |
| Dynamic local shots | Bounded circuit, measured outcomes and shot count | Optional Aer, <=12 wires/bits, <=10,000 shots |
| External equivalence | Backend-dependent | Optional QCEC, deadline and width/gate caps |

Examples of payloads only (not RSS or throughput):

| Qubits | One dense complex state | One dense complex operator |
|---:|---:|---:|
| 8 | 4 KiB | 1 MiB |
| 12 | 64 KiB | 256 MiB |
| 16 | 1 MiB | 64 GiB |
| 20 | 16 MiB | 16 TiB |
| 22 | 64 MiB | 256 TiB |
| 30 | 16 GiB | 16 EiB |

Operator sizes above eight qubits are theoretical, not supported Ketary
dense checks. Multiple arrays, conversion, scratch buffers, Python objects
and external workers increase actual memory. Dense algorithm cost is
exponential even if the API is simple. A future tensor-network, stabilizer
or hardware path changes assumptions and requires separate validation;
never silently substitute execution semantics.

## Extension rules

- New gate: registry, native builder/validation, replay/transform support,
  strict operator oracle and docs/stub coverage.
- New analysis: reuse Result, preflight inputs and work/output bounds,
  native/analytic comparisons; no simulation during query.
- New algorithm: ordinary Circuit factory; document promise, wire order
  and decoder interpretation; no opaque implicit run.
- New verification: distinguish mathematical scope, tolerance, resource
  bound, unsupported/inconclusive result; evidence schema review.
- New integration: private narrow adapter, lazy optional import, explicit
  opt-in and isolated CI; ADR and compatibility matrix before public API.

## Review and measurement

Architecture acceptance is a gate, not a score: no eager import cycle,
native/optional boundary inventory maintained, public inventory/stubs match,
core-only execution works, mathematical regression suite passes, artifacts
install. For expensive paths compare equivalent workload outputs before
timing. Use benchmark.py and the controlled protocol in
[release validation](release-validation.md). Record raw samples, versions,
median/p95, peak RSS and workload bounds. No claim of improvement based
solely on reduced lines or shared CI.

Use [AGENTS.md](../AGENTS.md) as contributor guardrails and
[ADRs](architecture.md#8-architecture-decisions) as decision history.
