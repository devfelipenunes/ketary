# QContract — ten-cycle Contract-First consolidation

Status: candidate local Alpha methodology, not a public release. This
register complements the [N-front roadmap](n-front-roadmap.md), not the
runtime roadmap. Freeze the admitted mathematical domains and Qiskit
interoperability. No new engine, DSL, hardware targets or branding of
the distribution in this initiative.

## Fronts and ownership boundaries

M01 methodology; M02 contract design; M03 API ergonomics; M04 mathematical
semantics; M05 contract quality; M06 developer experience; M07 validation
and evidence; M08 method evaluation. Independent work may run concurrently
on separate branches; shared public API or qualification changes must be
serialized and requalified on the integrated tree.

## Ten development cycles

| Cycle | Parallel fronts | Deliverables | Exit gate |
|---|---|---|---|
| C01 baseline | M01 M07 | Merge qualified design canvas and study addendum; inventory status and existing tests | Exact PR heads, integrated CI, no unresolved required checks |
| C02 workflow | M01 M02 M06 | Canonical intent-to-evidence flow, reusable canvas, navigation and worked example | A newcomer can follow the steps; examples execute from installed wheels |
| C03 design | M02 M04 M05 | Ten existing patterns with scope, assumptions, blind spots and allowed variations | Each admitted family traced to reference; no unsupported inference |
| C04 ergonomics | M03 M06 M07 | Inventory constructor friction, typed parity, wire-order guidance, naming | Convenience only if same obligation identity, outcome and budget; invalid controls |
| C05 semantics | M04 M07 | Explicit input scope, phase policy, snapshot and composition boundaries | All-input vs zero-input controls; strict vs relative controls; independent small matrix oracle |
| C06 quality | M02 M05 M07 | Defect/allowed-variation classification, obligation ablation and unresolved control | All declared real defects detected; permitted variants accepted; no metric inflation |
| C07 learning | M01 M03 M06 | Progressive exercises, diagnostic decision guide, CI example and API review | Runnable tasks; capture stumbling blocks without claiming external usability |
| C08 case studies | M02 M04 M05 M07 | Three distinct admitted-domain cases (state prep, clean logical action, observable rewrite) with fixed independent expectations | All cases reproduce; report counts and scope, not arbitrary algorithm correctness |
| C09 evaluation | M05 M06 M08 | Matched A/B/C tasks, scoring rubric, preregistration candidate and held-out task protocol | Independent review required for external phase; author smoke tests separate |
| C10 integrated close | all | Evidence register, documentation audit, compatibility check, installed artifacts on three OS, unresolved backlog | Exact integrated revision qualified; external review and study explicitly open until real evidence |

## Recursive execution

For every cycle, record the requirement, scope, independent expectation,
implementation revision, exact CI head and actual observed evidence.
Predict the status vector before running a test. If a defect survives,
first determine whether the mutation really violates the intended scope;
then strengthen the obligation or correct the fixture, never change the
expectation merely to match engine output. If an allowed variation fails,
review whether the specification is overconstrained. If an unresolved
status appears, check domain and budget without interpreting it as PASS.
Repeat only the affected fronts and their dependents; then rerun integrated
regression. An unqualified candidate stays open; no fabricated completion.

## Required metrics

Report numerator AND denominator for seeded true defects detected and
allowed variants accepted; separate inconclusive, unsupported, invalid
input and invalid fixtures. Do not report mutation score on unresolved
cases as if they were decided. Record expected and observed per-obligation
status, snapshot/obligation identity, domain, budget and exact commit.
Developer time, repair attempts and API errors require actual observations;
author examples are not participant data. Compare equivalent scopes only.
No arbitrary minimum mutation score or performance target is asserted.

## Review gates

- C01–C08 engineering: no unapproved semantic/domain change, all declared
  controls pass their expected vectors, no required regression failures,
  all three installed-wheel environments and documented examples succeed.
- C09 external: independent task/rubric approval and real participant
  observations; remain open under #165/#462.
- C10: integrated validation is separate from branch qualification.
  Release acceptance (#35) and controlled performance (#100) remain
  independent. Do not tag or publish a version.

## Initial execution register

#537/#538 are integrated. #539/#540 passed their respective 3 platform
qualification and 6 general SDK jobs before integration. Final integrated
tree qualification must still be inspected. C02–C08 have prior partial
evidence; do not equate this roadmap with ten completed development
iterations. C09–C10 retain their independent evidence gates.

Use [the design canvas](contract-design.md), [the method](methodology.md),
[quality controls](testing.md), [the scope review lab](scope-review-lab.md)
and [evaluation protocol](method-evaluation.md) as the working documents.

The [five recursive review rounds](five-review-rounds.md) refine C03–C08
with executable sufficiency, minimality, composition, evolution and
failure-diagnosis controls. Their qualification is tracked separately.
