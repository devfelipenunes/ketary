# Ketary Core: design contract (experimental)

Build, understand, verify. The core is a recommended subset of the same
existing Python API, not a separate package, facade, compiler or execution
mode. Four concepts: Circuit (program), Result (snapshot), Observable
(what to measure mathematically), Contract (reusable expectations).

```python
import ketary as q
c = q.bell()
r = c.run()
XX = q.X(0) @ q.X(1)
c.contract(expectations={XX: 1}).verify(r).require()
```

## Canonical path

| Intent | Prefer | Other supported paths |
|---|---|---|
| Construct | Circuit(n), bell(), fluent gates | gates namespace, h_many |
| Reuse blocks | apply(block,wires=...) | compose returns an independent circuit |
| Execute | run() | analyze() is a compatibility alias |
| Understand | result.math.probabilities(), expectation(Observable) | full-width labels and explicit observable/variance methods |
| Verify | result.test.expectation(...).require(), circuit.contract(...).verify(result) | result.verify, grouped expectations |
| Diagnose | circuit.test.compare(reference), report.evidence | aligned trace, diff, native metrics |
| Native access | to_qiskit, from_qiskit | explicit append and transpile |

Core means the default learning path; Advanced means optional capabilities;
Native means explicit Qiskit interoperability; Compatibility means retained
older entry points. See the complete [surface inventory](api-surface.md).
Neither designation implies a stable release or hides methods from IDEs.

## The Zen of Ketary

1. Express the problem before the mechanism.
2. Prefer one canonical spelling; keep compatibility intentionally.
3. Mathematics should be recognizable and precise.
4. Execution is explicit; a Result never reruns a circuit.
5. Mutation and ownership are predictable.
6. Complexity and costs are progressive, not invisible.
7. Verification always states its scope.
8. Keep native interoperability and bit ordering.

## Ownership and cost

Fluent gates, append, apply, measure/reset and reversible composition mutate
the builder and return it. Register/checkpoint record local annotations.
Compose, bind, inverse, copy, optimize, decompose and transpile return
independent circuits; copy preserves annotations, other transforms do not.
Global phase changes can invalidate checkpoint annotations. Result and
Observable are defensive snapshots/immutable expressions. Native exports
return copies. Report dictionaries remain mutable for legacy JSON compatibility.
Run, run_shots, sweep.run, trace, comparison and reproduction are explicit
potentially costly operations. Payload bounds are not RSS guarantees.

## Numerical meaning

Full-width labels are highest-wire-first; ordered subsystems follow caller
order. X/Y/Z/I use absolute wire indices; @ is restricted to disjoint
nonidentity support, not arbitrary matrix multiplication. Statevector Result
is ideal/pure; ShotResult is empirical and not interchangeable. State checks,
distribution checks, full operators, selected-input comparisons, external
QCEC and statistical checks have distinct guarantees. No formal proof or
root-cause guarantee. Always inspect status or require; not bool(report).

## API evolution

For each API change state the intent, canonical spelling, mutation,
execution cost, return type, error contract, scope, compatibility effect,
and native mathematical oracle. Add a function only if a demonstrated
workflow cannot be expressed adequately with existing abstractions.
See [compatibility](compatibility.md) and [acceptance](core-acceptance.md).

For implementation boundaries and ownership flows, see [architecture](architecture.md).
