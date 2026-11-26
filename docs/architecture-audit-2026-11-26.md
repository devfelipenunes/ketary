# Architecture audit — 2026-11-26

Baseline: fd8973813cbe5db1c0098a2a9c807a69da863fdc (PR #43 integrated).
Scope: architecture, coupling, resource contracts, API scalability and
extension governance. Static source review of all 25 flat Python modules,
existing tests and post-merge CI logs; no new benchmark or independent
review. This is an engineering audit, not a security certification.

## Baseline evidence

[Post-merge CI](https://github.com/devfelipenunes/ketary/actions/runs/45755230726)
completed successfully: six jobs, 489 core tests, 500 including Aer, 94%
branch-inclusive coverage, strict mypy consumer passed. Core/optional import
guard, native/analytic oracles, installed wheels and diagnostic benchmarks
passed. Dedicated-host data remain unavailable.

25 Python modules, 3,196 physical lines (including blanks/comments, excluding
trailing whitespace-only lines). Count unique internal source-target edges
from explicit relative import statements, distinguishing top-level and
function-local statements; no dynamic-import or runtime call-graph analysis.
92 edges total, 55 top-level edges, no top-level cycles; one 13-member
strongly connected component including function-local imports:
_checks, _circuit, _contracts, _ergonomics, _execution, _external,
_inspection, _plan, _reports, _result, _trace, _transpilation, _verification.
A strongly connected component is mutual reachability, not proof of recursive
runtime execution or failing initialization. _validation has 20 direct
incoming module dependencies, _circuit 9 and _result 6; _circuit has 16
outgoing dependencies. _circuit 633 lines, _result 454. Size alone is not a defect.

## Findings and prioritized follow-up

| ID | Priority | Evidence | Action and acceptance |
|---|---|---|---|
| AUD-A01 | P0 scalability | _ergonomics._single copies entire existing circuit for each ordered batch; bound copy revalidates. Circuit.apply uses non-inplace compose, then commits. Repeated small batches/blocks can sum growing prefix copies, potentially quadratic construction work. | Measure 100/1,000/10,000 equivalent appended gates/blocks against scalar/native paths. Design validated append-only staging or rollback preserving failure atomicity, phase, mode and annotations; test native full operator on small cases and no mutation on invalid inputs. Do not claim a speedup without measurements. |
| AUD-A02 | P1 coupling | 13-module SCC; _result imports _checks, _contracts, _ergonomics locally while these depend directly/indirectly on Result and Circuit. | Extract independent value/check result and wire/Pauli validation helpers only where they remove real reverse dependencies; isolate pure numerical comparison from circuit orchestration. Preserve public identities, stubs, schemas. Record graph before/after; no new SCC growth without rationale. |
| AUD-A03 | P1 resource model | _result.observable can evaluate 256 full-state Pauli queries; aggregate predicates up to 32, so theoretical 8,192 term evaluations per contract. QueryPlan.estimate counts dense payloads, then run materializes real/imag Python lists. Payload cap is not total memory/time. | Document per-operation work and retained-output contracts, quantify conversion/copy overhead; test preflight and simulation counts. Review any additional caps for compatibility rather than silently changing them. |
| AUD-A04 | P1 semantic consistency | compose/apply/append and _selection reject unordered wire containers; legacy h_many, mcx and math marginal/density/Schmidt accept iterable sets. QueryPlan subsystem construction also accepts them. | Decide canonical ordered-wire policy; test reversed mappings, generators, duplicates, unordered sets, bool and bounds. Any tightening of previously valid inputs needs explicit migration approval. |
| AUD-A05 | P1 dependency enforcement | Eager import guard intentionally ignores function bodies; AGENTS.md foundation/no-facade rules apply more broadly. Existing AST inventory protects external imports only. | Guard foundation and private-to-facade restrictions across all explicit imports; record allowed local back-references and report SCC changes. Preserve lazy optional integrations. No blanket ban on all local imports. |
| AUD-A06 | P2 ownership/documentation | Circuit is mutable, reports legacy mutable dicts; call-local cursor accesses authoritative native circuit. No declared thread-safety contract. Roadmap/ADR004 still say candidate after merge. | Document caller ownership and no concurrent mutation/execution guarantee; use per-caller independent copies when needed, no implicit locks/workers. Align roadmap status with integrated code. |

No P0 correctness failure or critical exploit was demonstrated by this audit.
P0 above means highest next engineering priority, not confirmed outage.
The proposed changes are not implemented here.

## Diagnostic performance (existing shared CI only)

Representative median times from post-merge benchmark logs, milliseconds:

| Workload | Native | SDK | Delta |
|---|---:|---:|---:|
| Build 1,000 gates, 8 wires | 2.683 | 2.992 | +11.5% |
| Build 10,000 gates, 8 wires | 26.851 | 29.856 | +11.2% |
| Mixed build 10,000 gates, 8 wires | 28.495 | 34.178 | +19.9% |
| Fluent build 1,000 gates, 8 wires | 2.840 | 4.298 | +51.4% |
| Ideal state, 16 wires / 64 gates | 36.902 | 37.053 | +0.4% |
| Full trace, 8 wires / 128 gates | 2.720 | 3.774 | +38.7% |

The existing fluent benchmark measures scalar gate calls, not repeated batch
or apply amplification. SDK performs additional validation/snapshot work.
These are diagnostic observations on shared CI, not controlled regressions or
speed superiority; retain raw timing/RSS artifacts. Dedicated host remains
required for release. Add repeated-block/batch cases before optimizing.

## Architecture decision

Retain the in-process modular SDK and Qiskit authoritative representation.
Do not create a second IR, general backend, separate API, dependency-injection
framework or distributed execution. Prioritize AUD-A01/A05 then AUD-A02/A03
and semantic policy AUD-A04. ARCH04 is now a concrete change-pressure review,
not a mandate to split every large module. ARCH05 dedicated benchmarks and
ARCH07 portability remain pending/deferred. No public release or new algorithms.

Review against AGENTS.md and ADR001–004. Each change is a separate PR with
native equivalence, resource contracts, compatibility and exact-head CI.
