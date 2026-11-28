# Quantum Contract-First — practical programming guide (candidate)

This guide consolidates the method for the existing QContract local Alpha.
It is not a new logic, an independently validated usability claim, a new
runtime API or hardware guarantee. Install both qualified wheels from the
same commit as described in the [installation guide](../qcontract-alpha-guide.md).

## The workflow

| Stage | Developer's deliverable | Review gate |
|---|---|---|
| 1. Design | independent requirement, scope, wire roles, phase policy | distinguish intent from implementation |
| 2. Specify | named Plan using admitted predicates | clarify blind spots, reject unavailable claims |
| 3. Challenge | predicted positive, defective, permitted and unresolved fixtures | classify scope before observing results; investigate sufficiency and redundancy |
| 4. Implement | source circuit and explicit module boundaries | never derive expected values from candidate measurements |
| 5. Verify | fresh prepared snapshots, local and final results | accept only required PASS in the intended domain |
| 6. Diagnose | report, route, domain, work budget, evidence/replay where supported | distinguish FAIL, INCONCLUSIVE, UNSUPPORTED and invalid inputs |
| 7. Evolve | independently reviewed intent and revised source | rerun controls; retain source revision, artifact identity and reports |

## Worked algorithm: coherent Bernstein–Vazirani

The [executable lab](practical_rounds.py) uses three logical data wires,
one workspace wire and a fixed three-bit secret. The coherent preparation
and parity-oracle algorithm uses only the admitted H, X and CX gates.
The ideal zero-input final state has the secret on the data wires and
the workspace returned to zero. There is no measurement, hardware
execution or quantum speedup claim in this exercise.

The contract is authored from the independent classical secret, not the
gate sequence: signed Z stabilizers on each data wire plus positive Z on
the workspace. These four independent stabilizers fix the ideal final
pure state up to global phase. In Qiskit, wire 0 is the least significant
bit; explicit mask authoring avoids reversing string labels.

A separate oracle module verifies selected all-input Pauli transformations.
The module's four checks are not a complete unitary specification; they
are deliberately scoped to the chosen observable requirements. A correct
oracle alone cannot establish the final algorithm's workspace cleanup.

## Five additional development rounds

| Round | Practical deliverable | Expected checks |
|---|---|---|
| R11 algorithm | fixed secret, intended output before implementation | 5 fixtures, 20 status comparisons with statevector cross-check |
| R12 modularity | independent parity-oracle contract and final output contract | 3 oracle fixtures, 12 comparisons with matrix cross-check; correct module but defective final cleanup |
| R13 reuse | typed project-local factories for all three-bit intents | 8 secrets, 32 output obligations, independent basis-distribution oracle and 8 invalid-input controls |
| R14 agent handoff | trusted intent frozen outside the candidate | one allowed rewrite accepted; five bad/weak/unresolved submissions rejected |
| R15 consolidation | this guide, runnable examples and evidence registration | integrated installed-wheel CI; previous review and workflow rounds remain enabled |

These are expected results until exact-head CI runs. The small numerical
oracles are independent cross-checks, not the engine's exact proofs.
The examples are teaching cases, not externally held-out tasks.

## Handoff checklist for a coding agent

Give the agent an explicit requirement ID, admitted domain, input scope,
wire mapping, allowed variations, immutable expected contract and
independent positive/defective controls. Ask it to propose source code,
not to replace the trusted expectation. An independent harness must
prepare the actual candidate and verify it against the reviewed intent.
A passing result about an old snapshot is not evidence for changed code.

The example checks the candidate Plan structurally and reconstructs
the expected Plan from the trusted secret. It cannot secure execution
of arbitrary untrusted code, and does not constitute a general agent
sandbox, authorization protocol or signed provenance system. Human
approval is required when the mathematical requirement changes.
No claim about real agent productivity follows from these synthetic
submissions.

## Running and navigation

Run `python -I docs/qcontract/practical_rounds.py` from an isolated
installed-wheel environment; retain contract-practical-rounds.json
from the qualification job. Review the individual reports, not only
the top-level workflow outcome.

Start with the [tutorial](tutorial.md), [design canvas](contract-design.md),
[pattern review](pattern-review.md) and [practice tasks](practice.md).
For quality and traceability, follow [rounds 1–5](five-review-rounds.md),
[rounds 6–10](workflow-rounds.md), [CI guide](how-to.md) and the
[ten-cycle roadmap](ten-cycle-roadmap.md).
The [candidate scientific evaluation](method-evaluation.md) remains
open for independent reviewers and participants.
