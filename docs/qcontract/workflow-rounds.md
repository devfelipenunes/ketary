# Contract-first developer workflow: rounds 6–10

These author-created exercises extend the ten-cycle roadmap without a
new public API or mathematical domain. Execute with the qualified wheels:
`python -I docs/qcontract/workflow_rounds.py`. The qualification artifact
is contract-workflow-rounds.json. Expected outcomes require exact-head CI.

## R6 — Authoring from intent

Before writing any circuit, declare the requirement: CNOT with logical
control 0 and target 1, for all inputs, up to common global phase.
Its action on the four independent Pauli generators is fixed before
implementation. The exercise verifies original, triple-CNOT rewrite,
missing gate and reversed wires against a numerical matrix oracle.
Expected: sixteen status comparisons; two acceptable and two defective
circuits. This does not validate an arbitrary algorithm.

## R7 — Signed and explicit-wire ergonomics

S maps X to Y and Y to -X in the forward direction. The transition
predicate is U† B U = A; therefore use A=-Y, B=X or A=X, B=Y.
Check both label and signed-mask forms under two budgets and compare
full report and status-only queries. Out-of-width support is an input
exception, not a false mathematical claim. Use explicit indices when
wire-order ambiguity matters.

## R8 — Admission and actual unsupported domain

Six-wire strict equality is outside the current exact strict-domain
bound, whereas common-phase equality for the same admitted source is
available. The mixed plan expects PASS, UNSUPPORTED, PASS, FAIL.
Never report unsupported as either success or a refutation. A supported
weaker predicate may only replace an unavailable one after independently
reviewing whether it expresses the intended requirement.

## R9 — Traceability and source evolution

A prepared snapshot is immutable; a mutable circuit edit does not
invalidate an existing report about its old snapshot. The exercise keeps
the same obligation while editing the source and verifies both snapshots.
Expected: old PASS, unchanged old PASS, edited FAIL, supported replay.
A pipeline must bind evidence to the actual candidate source revision.

## R10 — Fail-closed evidence gate

A project-local example compares the actual plan to an independently
reviewed plan, verifies afresh, checks result manifest and snapshot
identity, and accepts only all PASS. A review found that comparing
names alone would admit same-name substitutions; the refined gate
compares the mathematical specifications as well. Four negative
controls: missing obligation, same-name changed specification,
unresolved budget and refutation after edit.

This example is deliberately limited to the shown transition contracts:
it is not a general authorization mechanism, signed provenance system,
or proof that requirements are complete. Persist the reviewed plan,
source commit, wheel hashes, configuration, budget and reports in real CI.
A saved JSON report is not permission to skip fresh verification.

## Handoff to developers and coding agents

1. Read the [design canvas](contract-design.md) and write the required
   scope, wire roles, phase policy and expected behavior independently.
2. Select admitted predicates and record what they do not establish.
3. Freeze the reviewed plan and expected positive, defect, allowed and
   unresolved controls; don't weaken the plan to pass a test.
4. Implement, prepare the actual candidate, verify, diagnose and refine.
5. Record exact evidence and repeat after source edits. Request human
   review for a changed mathematical requirement or unresolved scope.

Do not infer external developer or agent productivity from this exercise.
The candidate [evaluation protocol](method-evaluation.md) remains subject
to independent review and real participants.
