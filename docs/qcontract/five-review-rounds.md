# Five recursive contract-review rounds

These exercises refine the existing ten-cycle roadmap. Each round has a
separate implementation commit; the shared script is qualified as one
candidate. No new public API, mathematical domain or user-study result.

| Round | Review question | Expected evidence |
|---|---|---|
| R1 sufficiency | Can the intended Bell state contract detect seeded bit and phase errors without rejecting legitimate rewrites? | 6 fixtures, 12 status comparisons, 3/3 defects refuted, 2/2 allowed variants accepted |
| R2 minimality | Does each intended obligation add useful coverage in this fixture set? | Actual removal of each obligation: 2/3 defects each vs 3/3 jointly; duplicate label adds no detections; same mathematical ID |
| R3 composition | Do local checks imply the overall guarantee? | 3 local checks; 4 final matrices, 2 compatible and 2 incompatible combinations |
| R4 evolution | Does a frozen intent survive implementation changes and an allowed common phase? | 4 revisions, 12 status comparisons; observable intent accepts 3 revisions, refutes 1; strict diagnostic distinguishes negative phase |
| R5 diagnostics | Can a developer distinguish refutation, resource exhaustion and invalid input? | Same snapshot and obligation across budgets; supported replay; invalid wire rejection; synthetic UNSUPPORTED classifier control |

Run from a qualified installed-wheel environment:
`python -I docs/qcontract/review_rounds.py`. The CI artifact is
contract-review-rounds.json. Expected outcomes are not observations until
the exact candidate passes. Retain individual reports and scopes.
A refuted conjunction may contain unresolved obligations; do not erase
those individual statuses. A permitted rewrite passing is a successful
control, not a missed defect. Mutation coverage of a finite fixture set
does not prove general sufficiency or minimality.

## Recursion

R1 establishes intended scope before implementation; R2 actually ablates
the obligations from R1; R3 checks a separate overall requirement instead
of relying on local success; R4 freezes the observable intent while
changing snapshots; R5 tests the interpretation of failure and unresolved
results. If the observed evidence diverges from the independent oracle,
inspect the fixture, scope and engine route before adjusting anything.
The review script is a development aid, not a public API or a scientific
claim of improved usability.

See [ten-cycle roadmap](ten-cycle-roadmap.md),
[design canvas](contract-design.md), [scope review lab](scope-review-lab.md)
and [evaluation protocol](method-evaluation.md).
