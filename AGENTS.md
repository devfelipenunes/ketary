# Ketary engineering instructions

These instructions apply throughout the repository. Read the canonical API
and architecture documents before modifying implementation. Do not infer
authorization for publication or new product scope from this file.

## Mission and scope

- Build a high-level Python SDK for quantum programs users can understand
  and verify. One public API, four core concepts: Circuit, Result, Observable,
  Contract. Prefer fluent gates, explicit run, mathematical expressions and
  typed verification reports.
- Experimental 0.1.0.dev0, Python 3.12.x only; keep .python-version and
  >=3.12,<3.13 aligned. Qiskit QuantumCircuit is authoritative. No second
  mutable IR, simulator, generic compiler, DSL, CLI, hardware execution,
  plugin system, service or publication in this scope.
- Use English in code and public documentation. Never include private
  workspace URLs, credentials or personal information.

## Architecture and ownership

- Read docs/architecture.md, docs/architecture-boundaries.md,
  docs/architecture-roadmap.md, docs/core-api.md and docs/compatibility.md.
  Keep ADRs and tested direct-import inventory current.
- Modular in-process SDK, selective ports/adapters, not strict backend
  independence. Keep one facade. Introduce a boundary only for concrete
  duplication, coupling or testing problems.
- _adapter owns native validation; _execution owns ideal evolution;
  _classical owns optional Aer; _external owns optional QCEC. Preserve
  lazy optional imports. No generic backend protocol without an approved
  second use case and a semantic compatibility design.
- _validation and _gate_specs are foundational and must not import other
  Ketary modules. Do not introduce eager internal import cycles or import
  the public package from private modules. Local imports are documented
  back-references, not dependency inversion.
- Builder mutations are explicit and atomic for validated batches; transforms
  return independent circuits. Result is a defensive snapshot; Observable
  and Contract immutable. Preserve annotation lifecycle and legacy report
  dictionary semantics. No implicit rerun, caching of mutable circuits,
  global mutable state, implicit threading or backend selection.
- Preserve little-endian ordering, global phase, strict/native/selected-input
  verification distinctions, and error/status semantics. Unsupported is not
  PASS. A witness is not proof of cause. Never loosen a numerical oracle.

## Scalability rules

- Identify input bounds, worst-case allocation, number of simulations,
  retained output size and time/work complexity. Validate budgets before
  expensive native calls or materializing unbounded iterables.
  Existing max_bytes contracts count selected payloads, not process RSS.
- Dense statevector: 16*2**n bytes; dense complex operator: 16*4**n bytes.
  Traces/sweeps retain multiple snapshots. Prefer monotonic checkpoint
  evolution, targeted queries and explicit streamed math where compatible.
  Never switch semantics or silently increase caps to accommodate workloads.
- Separate architectural growth, API growth and computational scaling.
  No blanket performance or backend portability claims. Benchmark equivalent
  workloads, versions, raw timings, median/p95 and isolated peak RSS.
  Shared CI is diagnostic, not controlled hardware evidence. Avoid noisy
  timing assertions. Record new allocations/copies and their rationale.

## Change workflow

1. Identify intent and roadmap ID; inspect existing API, tests and ADRs.
2. Choose the smallest coherent private change. For material dependency,
   ownership or execution changes, record an ADR and update the module map.
   New public APIs require justification, type stubs, surface classification,
   compatibility review and explicit scope approval.
3. Add native/analytic regression oracles, negative/boundary tests,
   compatibility and optional-backend checks as relevant. Keep existing
   checks; no skipping/weakening tests to pass CI.
4. Run python -m pytest -q -rs tests research/probes, strict mypy consumer,
   full CI (tests, dynamic, dependency-review, external-verifier, benchmark,
   packaging). Follow docs/release-validation.md for controlled measurements.
5. Use a separate branch and PR. Describe actual results, limitations,
   resource contracts and migration implications. Owner permits merge
   commits after required exact-head CI and technical review. Never push
   directly to main, bypass protections or claim independent approval when
   review was performed by the same agent. Confirm integrated tree and
   post-merge CI; record outstanding items honestly.

Production/distribution requires controlled dedicated-host benchmarking,
reviewed PoC/RFC, artifact and third-party notice/license review and explicit
owner approval. Do not tag, upload or publish. Preserve Apache-2.0 and
third-party notices.
