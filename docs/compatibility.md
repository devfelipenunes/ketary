# Experimental compatibility and evolution policy

The package remains 0.1.0.dev0; no stable 1.0 commitment. Python 3.12.x and
the declared Qiskit dependency are the supported development target.
Preserve existing public call signatures, defaults, valid behavior, report
keys and logical replay unless a documented correctness/security reason or
an explicitly approved migration requires change. New accepted inputs must
not change old inputs' semantics. Existing legacy aliases (gates, h_many,
analyze, JSON dictionary access) remain available; recommend the canonical
path in new examples. No removal or deprecation warning in this cycle.

For a proposed breaking change record the old/new behavior, migration path,
affected callers and schemas, release boundary, and regression tests.
Require owner approval before breaking compatibility or public distribution.
Do not introduce another wrapper namespace to solve naming redundancy.
Experimental internals (underscore names) are not public contracts.

Verifications: status, require, render and explicit exports are the common
interface for verdict reports. Preserve legacy bool behavior (CheckResult
raises; dict reports and VerificationReport do not use truth as verdict).
Do not standardize distinct result schemas by silently changing their scope.
SemanticDiffReport has no single verdict. Empty legacy Result.verify remains
UNSUPPORTED; empty reusable Contract remains invalid. ResourceLimit and
UnsupportedOperation are ValueError subclasses; invalid values raise
ValueError, wrong object/mapping types raise TypeError where established.
Non-PASS require raises AssertionError. Preserve numeric tolerances.

Logical replay schema v1 remains unchanged. Contract.to_dict preserves the
existing fields and adds observable_expectations only for new expression
predicates. It is an export, not an import API. Legacy report keys remain
unchanged; report keys for new observables encode the embedded term mapping.
Never claim cross-version numerical reproducibility solely from version labels.

CI requires signature parity, public export inventory, native or analytic
oracles, legacy regressions, canonical examples and clean installation.
No tag, publishing or independent usability claim follows from passing CI.
