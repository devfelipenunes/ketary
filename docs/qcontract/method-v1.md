# Quantum Contract-First — method v1.0 candidate

This document consolidates the existing local Alpha methodology. The
version labels the proposed method, not an SDK release or a claim of
independently proven superiority. Qiskit remains authoritative for source
circuits. The engine's admitted domains are frozen for this consolidation.

## Required workflow

1. Record the mathematical intent and independent expected behavior.
2. Declare scope, wire roles, phase policy and permissible variation.
3. Choose named obligations from the admitted predicates; document
   their limitations and any redundant diagnostic checks.
4. Design positive, real-defect, allowed-variation and unresolved
   controls before implementing the circuit.
5. Keep requirements separate from implementation; verify local
   components and the assembled circuit in fresh prepared snapshots.
6. Compare expected and observed outcomes. Reject refuted, unsupported
   and inconclusive required obligations; input exceptions are not verdicts.
7. Retain source revision, artifact hashes, domain, snapshot/obligation
   identities, budgets and reports. Repeat after changes. A changed
   requirement requires independent review.

The [design canvas](contract-design.md), [pattern review](pattern-review.md)
and [practical guide](practical-guide.md) provide the working templates.
Use the [reference](reference.md) to check admission before authoring.

## Example project architecture

- [requirements.py](project_example/requirements.py): independent intent,
  exact rational observable specification, module requirements and
  logical action reference.
- [implementation.py](project_example/implementation.py): candidate
  compute, phase and uncompute modules, independent of the requirements.
- [verify.py](project_example/verify.py): fresh-snapshot verification,
  independent small numerical oracles, diagnostics and fail-closed gate.

Run `python -I docs/qcontract/project_example/verify.py` using the installed
qualified wheels. This is a trusted local example, not a new project
framework or sandbox. Requirements and implementations should be reviewed
separately; executing arbitrary candidate Python code is not made safe by
contract checking.

## R16–R20

| Round | Evidence expected |
|---|---|
| R16 expressivity | Rational weighted noncommuting Pauli sum; four circuit controls and independent matrix cross-check |
| R17 modularity | Compute-phase-uncompute gadget implements logical T for initially clean workspace; five final fixtures, fifteen comparisons; local phase invariants deliberately cannot distinguish T from Tdg |
| R18 architecture | Separate requirement, implementation and verification modules; one accepted project and three rejected controls |
| R19 ergonomics | Three equivalent authoring forms on two circuits and two logical budgets; identical reports |
| R20 audit | Inventory of all 18 executable rounds plus R15 and R20 documentation milestones, exact checkout SHA and required file presence |

The logical T reference is the direct T on wire 0 with wire 1 initially
zero. The gadget need not equal that reference on the full register.
Cleanup is implied by matching the clean-subspace reference, but is
retained as a diagnostic. The strict whole-register check is optional and
must not determine acceptance. The two local Z invariants do not specify
the full phase transformation.

The example deliberately adds no runtime predicate, API abstraction or
general sequential proof calculus. Dense numerical oracles are limited
to one and two qubits. No hardware claim or controlled speed comparison.

## Consolidation gates

The [audit script](audit_method.py) checks the presence and expected keys
of four same-job JSON artifacts and the required methodology files.
It records the exact checkout SHA; it is an inventory, not an independent
proof of the engine or of user productivity. All scripts must first pass
their executable assertions on installed wheels. PR and main qualification
remain separate; main qualification is triggered on relevant pushes.
Keep the general SDK regression jobs and all previous checks.

C01–C08 engineering evidence is candidate until exact integrated CI passes.
C09 requires independent reviewer approval and real participants;
C10 requires integrated qualification and explicit outstanding issues.
See [evaluation](method-evaluation.md) and [roadmap](ten-cycle-roadmap.md).
Do not close #165/#462, release #35 or controlled performance #100 based
on this author-created work. No release tag or registry publication.
