# CDQP-P01: research effect contracts

Practical research prototype, not public API, novel logic or formal proof.
Existing Contract remains a snapshot predicate. Effect obligations are
different: for a terminating CPTP map E, check A <= E*(B)+atol I.
A and B are effects (0<=A,B<=I), not arbitrary observables.
A positive spectral residual beyond tolerance and diagnostic guard has
a constructive pure-input witness. A near-boundary result is inconclusive.
Numerical admission and gray band are not certified floating-point bounds.
Reports retain residual, witness, scope, canonical numerical matrix hashes
(not authentication signatures), tolerance and admission defects. Hashes bind
evaluated symmetrized matrices, not original raw inputs. Record exact source
revision and dependency environment separately. No import/replay API.

Run with installed pinned SDK: python research/effect_contracts.py.
Bell preparation obligation with pre=|00><00|, post=|Phi+><Phi+|.
Mutant Z on output gives a failure witness. This obligation is not full
operator equality; Z before preparation can preserve it. Native adapter
explicitly converts bound unitary Ketary circuit through public to_qiskit
and Qiskit Operator. No automatic verification/execution from builders.

Independent checks: Hadamard, amplitude damping, composition (two local
checks and a direct composed check), invalid inputs, phase/domain, witness
recalculation, immutable report and hash binding, real Ketary/Qiskit adapter.
Neither snapshot nor effect claims replace the other.

Resource scope: 1..5 qubits, ndarray square dimensions 2..32, 1..16 Kraus
matrices, <=256 native instructions. Matrix payload 16*d*d bytes, <=16KiB
at d=32; bounded matrix lists, O(k*d^3+d^3) algebra and native scratch
not an RSS guarantee. No arbitrary iterables, no dense construction before
width preflight. Square same-dimension channels only; no conditioning,
loops, general partial correctness, formal verification, hardware, new IR,
public API, dependency or package changes. Composite Kraus count capped
before construction. Direct composite check is independent of local PASS.

Next gates: actual exact candidate CI, raw artifact audit; demonstrate
clean-ancilla postcondition with domain and repair; compare usefulness
against direct dense NumPy/Qiskit checks at matched guarantee strength;
then decide whether a public interface earns its place. No merge until
review, no release.

## Composite application study

Five-wire Grover search with a parity-and-conjunction oracle, two marked
data states (13 and 14), one workspace wire, and a separate diffuser.
Twelve correct/defective variants distinguish workspace restoration,
logical action on the clean-workspace subspace (up to common phase),
and joint marked-state/clean-workspace probability. Two distinct oracle
implementations and a global phase control are accepted. An independent
truth-table diagonal oracle and analytic reflection supply reference
matrices; exact expected probabilities and failure categories are fixed.
A missing uncompute, wrong clause, identity oracle, wrong/identity diffuser
and under/over-iteration must be distinguished. Effect residual and
logical restriction residual are different numerical criteria; only
classification of these well-separated examples is compared.
No public API change. This is a small ideal simulation, not proof of
scalable verification or actual user productivity.

Two additional adversarial variants swap unmarked states 0 and 1 after
an otherwise valid oracle or diffuser. The search still succeeds with
probability .9453125 from uniform input, but the relevant logical action
contract fails. The distinction matters for reusable subroutine semantics;
these are not algorithm-outcome failures. No claim of detecting more bugs
than equivalent handwritten subroutine tests.
