# Contract-first development method

QContract 0.1.0a3, local Alpha. This is a practical workflow for the
existing restricted contract API, not a new logic or a proof of arbitrary
program correctness. Start with the [tutorial](tutorial.md) and
[reference](reference.md).

## Six steps

1. Specify the intended property and its scope before writing gates:
   all-input observable identity, zero-input state, clean workspace,
   reference equivalence, or one of the other admitted families.
2. Implement the smallest circuit satisfying the specification.
3. Prepare a fresh snapshot and verify the named Plan. A Plan is a
   conjunction of independent obligations, not a sequential Hoare proof.
4. Mutate the implementation, without rewriting the expected property.
   Include an analytically justified negative control. Surviving mutants
   are evidence of a potentially weak specification, not proof of a defect.
5. Diagnose FAIL using the reported domain, route, witness/expectation and
   supported replay. Keep INCONCLUSIVE and UNSUPPORTED distinct; never
   increase budgets blindly or mark these statuses as passing.
6. Execute only within the intended ideal-circuit scope. Reverify after
   editing. Hardware, noise and arbitrary transpilation are separate.

## Choose the guarantee

| Intent | Existing API | Avoid |
|---|---|---|
| Map an observable for every input | transition / Contract | Testing only the zero state |
| Preserve an observable | invariant | Confusing this with state stabilization |
| Prepare a specific correlation | zero_input / StateEigen | Claiming one stabilizer specifies a state |
| Restore initially clean ancillas | clean_ancillas / CleanInput | Assuming all wires were initially zero |
| Compare implementations | Prepared.equivalent_to / action_matches | Ignoring strict vs global phase and clean-input scope |
| Other admitted properties | Named with the typed families in reference.md | Treating them as arbitrary quantum assertions |

Use the same independent expectation for original and mutant. Do not
derive the expected value from the implementation under test.

## Example 1: a GHZ preparation with a deliberately incomplete test

Specify three independent commuting stabilizers of the intended
three-qubit GHZ+ state. For the ideal pure state these jointly determine
a one-dimensional stabilized subspace. The single Z correlation alone
does not.

```python
from qiskit import QuantumCircuit
from qcontract import Plan, zero_input, prepare

ghz_plan = Plan((
    zero_input("Global X coherence", stabilizes="XXX"),
    zero_input("Adjacent Z correlation 01", stabilizes="IZZ"),
    zero_input("Adjacent Z correlation 12", stabilizes="ZZI"),
))
ghz = QuantumCircuit(3)
ghz.h(0)
ghz.cx(0, 1)
ghz.cx(1, 2)
prepared = prepare(ghz)
assert ghz_plan.verify(prepared).require().passed

phase_mutant = ghz.copy()
phase_mutant.z(0)
mutant = ghz_plan.verify(prepare(phase_mutant))
assert [r.status for _, r in mutant.results] == ["FAIL", "PASS", "PASS"]
assert Plan(ghz_plan.obligations[1:]).verify(prepare(phase_mutant)).passed
assert ghz_plan.verify(prepared).passed
assert prepare(phase_mutant).snapshot_id != prepared.snapshot_id
```

The phase mutant changes GHZ+ to GHZ-, leaving the Z correlations intact.
This demonstrates why property choice matters. A second snapshot is
required; editing a source does not modify a prepared snapshot.

## Example 2: workspace cleanup is an all-logical-input property

```python
from qcontract import clean_ancillas, invariant

workspace_plan = Plan((
    clean_ancillas("Workspace returned to zero", wires=(1,)),
    invariant("Logical Z preserved", observable="IZ"),
))
uncompute = QuantumCircuit(2)
uncompute.cx(0, 1)
uncompute.cx(0, 1)
assert workspace_plan.verify(prepare(uncompute)).require().passed

missing_uncompute = QuantumCircuit(2)
missing_uncompute.cx(0, 1)
outcome = workspace_plan.verify(prepare(missing_uncompute))
assert [r.status for _, r in outcome.results] == ["FAIL", "PASS"]
```

The incorrect circuit still preserves Z on the control. The workspace
contract detects the missing uncomputation without requiring a particular
logical input.

## Example 3: a T phase gate with a bounded exact invariant

```python
phase_plan = Plan((invariant("Preserve computational Z", observable="Z"),))
phase = QuantumCircuit(1)
phase.t(0)
assert phase_plan.verify(prepare(phase)).require().passed

wrong_basis = QuantumCircuit(1)
wrong_basis.h(0)
assert phase_plan.verify(prepare(wrong_basis)).results[0][1].status == "FAIL"
```

This is not a proof that the circuit is exactly T: many diagonal gates
also preserve Z. Use equivalence to a reference if that is the actual
requirement.

## Example 4: equivalence and scope, plus a numeric independent control

```python
import numpy as np
from qiskit.quantum_info import Operator
from qcontract import Named

reference = QuantumCircuit(1)
reference.z(0)
implementation = QuantumCircuit(1)
implementation.s(0)
implementation.s(0)
ref = prepare(reference)
candidate = prepare(implementation)
equivalence = Plan((Named("Same gate-induced unitary",
                           candidate.equivalent_to(ref, strict=True)),))
assert equivalence.verify(candidate).require().passed
assert np.allclose(Operator(reference).data, Operator(implementation).data,
                   rtol=0, atol=1e-12)
implementation.x(0)
bad = prepare(implementation)
bad_plan = Plan((Named("Same gate-induced unitary",
                        bad.equivalent_to(ref, strict=True)),))
assert bad_plan.verify(bad).results[0][1].status == "FAIL"
assert not np.allclose(Operator(reference).data, Operator(implementation).data,
                       rtol=0, atol=1e-12)
```

The numeric comparison is a small independent cross-check, not an exact
proof or a scalable alternative to the contract engine. Reference and
implementation must both remain within the admitted domain.

See [test the quality of your contracts](testing.md) for an executable
mutation matrix, allowed variants, and scope-specific reference controls.

## Review checklist

- Name each obligation by intended behavior, not by gate sequence.
- Write the input assumptions and distinguish state vs operator scope.
- Check Qiskit's highest-wire-first label convention; use pauli_on for
  explicit wire indices when useful.
- Keep a positive control, a meaningful negative control, and an
  unresolved-budget control in regression tests.
- Use require() only when all obligations must pass. Never mask unresolved
  statuses in CI. A property can pass while the whole program is wrong.
- Store source revision, snapshot ID, obligation ID, status and budget.
  Keep full reports when evidence matters; statuses() omits reports.

All Python blocks in this page are intended to execute in order against
the installed candidate wheels. These are developer-authored examples,
not evidence from an external developer usability study.
