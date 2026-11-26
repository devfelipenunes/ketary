# ADR 004 — Consolidate native execution and trace evolution

Status: implemented in #43; exact-head and post-merge CI passed.

Context: Circuit.run combines public mode/budget validation with native
state creation/evolution, and tracing duplicated zero-state/global-phase
initialization and gate iteration across four paths.

Decision: keep mode and payload preflight in Circuit.run; delegate ideal
native evolution to _execution.execute_ideal. Reuse the existing private
monotonic _Cursor for trace, checkpoint, aligned comparison and grouped
checks. No generic backend interface. Keep public signatures, returned
snapshots, exact phase, order, error and budget semantics.

Consequences: fewer duplicated execution mechanisms, one trace progression
path, no additional public abstractions. Resource caps remain conservative;
no measured speedup claimed. Existing native and analytic tests plus prefix,
complex-state, preflight and early-stop regressions guard semantics.

## Candidate follow-up: prepared batch dispatch

An explicitly preflighted run_many batch may reuse exact Result snapshots and
ordinary basis labels without repeating width, input normalization and payload
admission checks for every native evolution. Subclasses retain the old checks.
The total batch payload admission and complete input preflight remain before the
first native call. No public signature or bound changes; no additional native
backend or persistent cache. Benchmark old and new end-to-end batch paths and
retain only if the candidate benefits the measured workload. Pending CI.
