# Verification guide

Choose a check by the question being asked; no one status has a universal
meaning independent of its scope.

| Method | Numerical criterion | Scope |
|---|---|---|
| Result.test.probability/expectation | scalar tolerance | one ideal snapshot |
| Contract.verify / Result.verify | selected predicates | one ideal snapshot |
| Result.test.state | maximum amplitude residual, optional phase alignment | two snapshots |
| Result.test.distribution | total variation | Z-basis distributions |
| Circuit.test.equivalent | maximum matrix element residual | complete small operators |
| Circuit.test.metrics | spectral norm under declared phase policy | complete small operators |
| Circuit.test.compare | state L2 witnesses then optional spectral norm | selected inputs and/or full matrices |
| Circuit.diff | structural and zero-input summary plus metrics | separate dimensions |
| Circuit.test.external_equivalence | native QCEC criterion | external up-to-phase relation |
| StatisticalContract.verify | simultaneous Hoeffding intervals | declared IID outcome events |

Strict operator checks preserve global phase by default. Optional common
phase alignment uses the complex overlap, not minimization of spectral
distance over all phases. Selected-input comparison aligns each state
separately when phase is ignored. No detected counterexample is not proof:
sample-only matching is INCONCLUSIVE. Numerical tolerance is not formal proof.
QCEC's result is separate from Ketary's strict-phase metric.

`CheckResult` is not truthy; use `.status` or `.require()`.
`VerificationReport.require()` raises for non-PASS. Dictionary reports
require explicit status inspection. PASS means only the declared criterion
passed; FAIL may mean a mathematical discrepancy or a dimension mismatch;
UNSUPPORTED means the requested method cannot evaluate the input; INCONCLUSIVE
means available evidence does not settle the requested question.
Invalid arguments raise exceptions. ResourceLimit and UnsupportedOperation
are ValueError subclasses. Not all methods return all four statuses.

Use `debug.verify_checkpoints({index: contract})` for selected zero-input
prefixes; a divergence is not proof of root cause. Evidence JSON has a
content hash, not an authentication signature. Reproduction runs explicitly;
greedy minimization preserves a fixed witness, not a globally minimal cause.
After each accepted deletion the scan restarts. If the attempt budget is not
exhausted, every single remaining gate deletion has been tested against the
same fixed input, phase policy, tolerance and reference. A single-deletion
local minimum need not be globally minimal. The reference is executed once;
there are two baseline ideal evolutions and at most one per deletion attempt.
The 128-attempt cap, payload preflight and report schema are unchanged.
See [roadmap contracts](verification-roadmap.md) for exact boundaries.

## Canonical usage

Use `.status` for branching, `.require()` for an assertion, `.render()` for a human-facing message and `.to_dict()` / `.to_json()` for explicit export of verdict reports. Legacy report truthiness and dictionary schemas are retained for compatibility; never infer PASS from `bool(report)`. SemanticDiffReport deliberately has separate dimensions and no aggregate status. A decoder's PASS denotes a unique mode, not verified algorithm correctness.

Single and aggregate expectation checks accept real Observable expressions as well as full-width Pauli strings. A plain local-wire mapping works for an individual check; use immutable Observable expressions as aggregate mapping keys. Mixed aggregates preserve legacy `expectation:XX` keys and use `expectation:observable:` followed by canonical embedded JSON for expressions. Contract export adds `observable_expectations` only when present; string-only exports are unchanged. There is no contract import or new replay format. Duplicate embedded expression keys are rejected. Numeric expectations for weighted sums are finite real values, not restricted to [-1,1].
