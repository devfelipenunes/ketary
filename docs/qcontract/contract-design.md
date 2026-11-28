# Quantum Contract-First — contract design method v0.1

A provisional practical method for the existing QContract Alpha.
The contract is designed before the implementation; verification is
restricted to admitted predicates. This is not a new logic, general
correctness-by-construction calculus, or claim of scientific priority.

## Design canvas (complete before coding)

| Field | Question |
|---|---|
| Intent | What observable behavior should this component guarantee? |
| Input scope | All inputs, all-zero input, clean ancillas, finite error set, or a reference? |
| Wire roles | Which wires are logical, workspace, or observed? |
| Allowed variation | Global phase? Different implementation? Changes outside the input subspace? |
| Obligation | Which existing predicate expresses the intended guarantee? |
| Sufficiency | Which wrong implementations could satisfy the same predicate? |
| Controls | Which independent good, defective, equivalent and unresolved cases should be checked? |
| Evidence | What status, snapshot, obligation, domain and budget must CI retain? |

### Design rules

1. Specify behavior, not the gate sequence used to implement it.
2. Make scope explicit. A zero-input property does not imply an
   all-input transformation. An all-input identity of one observable
   does not determine the complete unitary.
3. Use the weakest obligation that is sufficient for the declared
   requirement; add independent properties only to close real gaps.
4. Avoid redundant properties when a stronger property implies them
   for the same admitted scope. Redundancy can still be useful for
   diagnosis; label that purpose. Do not claim automatic implication
   or minimality checking.
5. A Plan is a conjunction, not a proof of sequential composition.
   Verify the final combined circuit separately when the requirement
   refers to its overall behavior.
6. Declare phase policy. Strict full-unitary identity, identity modulo
   global phase, and agreement on a clean subspace differ.
7. Keep specifications independent of the implementation; use an
   independent mathematical reference for small examples.
8. Never reinterpret invalid input, UNSUPPORTED or INCONCLUSIVE as
   PASS. An execution gate requires every intended obligation to PASS.

## Design patterns using the existing families

| Pattern | Existing predicates | Diagnostic blind spot |
|---|---|---|
| Prepare a target stabilizer state | StateEigen for independent generators | Missing generators can admit incorrect states |
| Transform an observable | Transition | One identity need not characterize the unitary |
| Preserve an invariant | Transition with equal pre/post | Other observables may change |
| Reuse clean workspace | CleanInput | Logical action may still be wrong |
| Refactor an implementation | Equivalent / RelativeAction | Phase or input scope must match intent |
| Check a bipartition | Separable | Says nothing about a specific target state |
| Reason about one hypothetical Z branch | ZBranch | Not arbitrary dynamic-circuit verification |
| Preserve a weighted observable | SumTransition | Rational bounded terms only |
| Check finite Pauli noise | NoiseAfter | Not arbitrary device noise |
| Check a finite error set | Correctable | Not hardware fault tolerance |

See [pattern review cards and anti-patterns](pattern-review.md) for a
copyable design record and scope-specific controls.

## Worked design review: clean workspace versus logical identity

Intent A: return workspace wire 1 to zero for arbitrary logical wire 0.
Intent B: leave logical wire 0 unchanged, up to a common phase on
the admitted clean-input subspace. These are independent requirements.
A single Z on the logical wire satisfies A, but violates B. A Z on
the workspace satisfies both A and B, yet is not the identity on
the entire two-wire register. This is why strict full-register
equivalence would overconstrain the intended specification.

| Candidate | CleanInput | RelativeAction to identity on clean input | Strict full identity |
|---|---|---|---|
| CX then CX | PASS | PASS | PASS |
| One CX | FAIL | FAIL | FAIL |
| Logical Z | PASS | FAIL | FAIL |
| Workspace Z | PASS | PASS | FAIL |

These are independently reasoned expected outcomes, not measured
candidate results. The [executable design review](design_examples.py)
checks these and three additional controls against the installed Alpha
and a small independent numerical matrix oracle during qualification. The existing mutation examples in
testing.md use a different explicit requirement (whole-register
identity); do not mix the acceptance criteria.

## Review gate

A design is ready for implementation review when its intended scope,
obligations, known blind spots, negative controls, allowed variation
and evidence policy are recorded. A circuit is ready for use within
that scope only after the required checks pass. Hardware, compilation
and external usability remain independent evidence requirements.

## Relationship to prior work

Design by Contract, quantum Hoare logic, QbC, QBricks and
property-based quantum testing are relevant predecessors. The proposed
contribution is a practical contract-design workflow over a bounded
existing Qiskit-compatible verification API. Novelty, productivity and
adoption are open empirical questions, not established results.

See methodology.md, testing.md and reference.md for the existing
executable foundation.
