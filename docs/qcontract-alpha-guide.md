# QContract Alpha — local candidate guide

Provisional name and API. The local distribution is qcontract-alpha-local;
the Python import is qcontract. Nothing is uploaded to a package registry.
This candidate depends on the local `qcontract-native-alpha-local` native wheel and Qiskit, not on the
previous SDK package. CPython 3.12 is the admitted interpreter.

## Install from validated local build artifacts

From a clean Python 3.12 virtual environment, install both wheels produced
by the alpha qualification workflow in a single pip command, allowing
Qiskit and NumPy dependencies to resolve. Use the exact wheels for your
platform. No production compatibility or public PyPI availability is
implied.

## First exact contract

```python
from qiskit import QuantumCircuit
from qcontract import Pauli, Contract, StateEigen, prepare

c = QuantumCircuit(2)
c.h(0)
c.cx(0, 1)
p = prepare(c, prepare_state=True)

transition = Contract(requires=Pauli("IZ"), ensures=Pauli("XX"))
state = StateEigen(Pauli("XX"))
assert p.check(transition).status == "PASS"
assert p.check(state).status == "PASS"
bad = Contract(requires=Pauli("IZ"), ensures=Pauli("-XX"))
failure = p.check(bad)
assert failure.status == "FAIL"
print(failure.witness)
```

The transition proves U-dagger B U = A for all inputs. The state contract
proves that the signed Pauli stabilizes U applied to the all-zero input;
one does not imply the other. Labels use Qiskit wire order (highest wire
first); Pauli returns integer masks, so leading identity characters do
not establish a width restriction. The prepared width bounds the masks.

## Exact admitted domains

| Contract | Semantics | Current bounds |
|---|---|---|
| Contract / Transition | All-input signed Pauli identity | 1–64 wires, bounded exact routes |
| StateEigen | Zero-input signed Pauli eigenproperty | 1–64 wires, optional prepared DAG and Heisenberg fallback |
| CleanInput | Zero leakage on all clean ancilla inputs | 1–64 wires, bounded projected route |
| Prepared.action_matches | Coherent clean-input action up to phase | 1–64 wires, combined snapshot cap |
| Prepared.equivalent_to | Full admitted unitary equivalence modulo phase | 1–32 wires |
| Prepared.equivalent_to(strict=True) | Strict packed gate-induced unitary equality | 1–5 wires, <=512 gates per circuit |
| Separable | Zero-input pure state rank-one across one cut | 1–5 wires, <=512 gates |
| ZBranch | Unnormalized zero-input Z measurement branch probability/expectation | 1–5 wires, <=512 gates |
| SumTransition | Rational Hermitian Pauli sums | <=64 terms per side, bounded exact propagation |
| NoiseAfter | Clifford followed by finite Pauli mixture | <=16 weighted entries |
| Correctable | Finite error-set code criterion and recovery synthesis | Code-only; no physical fault tolerance |

Equivalence counts as one family with two explicit phase modes. All
results are scoped to the admitted gate alphabet H, S, S-dagger, X, Z,
CX, T, T-dagger. A circuit may contain at most 100000 gates; individual
routes have stricter limits (e.g. T count, terms, state nodes). Parameterized
gates, measurement/reset instructions, classical bits, arbitrary rotations
and nonzero source global phase are rejected at preparation. ZBranch
describes a hypothetical exact Z instrument on an admitted unitary
snapshot; it does not execute arbitrary measured circuits.

## Results and budgets

PASS = exact guarantee in the stated domain; FAIL = exact refutation;
INCONCLUSIVE = bounded method could not finish; UNSUPPORTED = recognized
contract outside route scope. Invalid input raises ValueError/TypeError.
Do not convert INCONCLUSIVE to FAIL or PASS. Each batch admits 1–64
contracts with disjoint logical reservations (max_work <= 2000000).
Preparation caps are separate and state preparation is opt-in. Work is
not a CPU, bit-operation, memory, or wall-time guarantee.

Prepared snapshots are immutable and isolated from later source circuit
edits. A Result includes status, domain, snapshot and obligation IDs,
reserved work, route when supplied, and optional witness/evidence/exact
expectation. Diagnostic shapes are provisional, not a stable wire schema.
Prepared.replay independently checks native Clifford transition verdicts and their exact product-state witnesses, as well as selected other transition/state routes. None means
unavailable. Evidence is not authenticated or a succinct proof of work.
Other families do not yet offer portable replay.

## Validation and limitations

The historical research remains in the repository; the staging script
selects the needed runtime declarations and uses package-relative imports.
It does not execute benchmark-only ctypes loaders. Runtime manifest hashes
bind each generated module to its original source. Native backend is a
locally staged QContract wheel, not independently security-audited. No hardware
execution, arbitrary noisy circuits, general formal verification, external
usability validation, or production readiness is claimed.


## Typed API and benchmark evidence (A3)

The local candidate 0.1.0a2 includes a PEP 561 marker and public type
stub. IDE completion and type checking cover the ten specifications,
prepared session and Result. Run the isolated qualification workflow
to see positive and deliberately invalid mypy examples. Runtime
admission remains authoritative: Python type hints are not guarantees.
Canonical Qiskit gate concrete types are required; custom base_class
spoofing, open controls and modified mutable definitions are rejected.
This is an input boundary, not a sandbox for untrusted Python objects.

The installed benchmark compares signed Clifford identity verdicts with
Qiskit PauliList vectorized evolution, measuring cold preparation,
prepared verdicts and full reports separately. QContract also computes
witnesses/metadata; Qiskit baseline returns Boolean verdicts only.
The comparison uses shared CI hosts, not dedicated CPU performance.
