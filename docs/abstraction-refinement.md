# Second abstraction slice: evidence-driven refinements

Parent #167 / #141–#166. The first atlas run 45769743919 passed three
jobs (65 tests each, including Aer). All 27 tasks matched strict native
operators and arbitrary complex states; maximum candidate error
2.2221e-15. Authored lexical totals: current Ketary 687, candidate 681,
Qiskit 861. Candidate vs current: 14 shorter, 3 tied, 10 longer.
These tasks are not representative population statistics.

Selected first-run cases (current/candidate/Qiskit tokens):
aligned CP 34/19/32; Pauli XZ 39/10/28; increment4 42/8/48;
QAOA 47/81/50; QPE 12/99/67; VQE layers 32/52/43.
QPE construction 0.296/7.263/0.139 ms, QAOA 0.067/0.572/0.043 ms,
runner 1101 medians only. Candidate was not uniformly better.

Second slice:
- Exact single-Pauli RX/RY/RZ and same-axis pair RXX/RYY/RZZ instead
  of redundant conjugation/CNOT decomposition.
- Closed single-control research path tries standard gate controls,
  adding original global phase as P on control. Unsupported shapes
  explicitly use bounded native synthesis and strict full-operator
  verification. This is not a public fallback or automatic backend.
- Add bounded unitary amplitude and product state preparation, explicit
  truth-table bit-flip oracle, modular two-register adder, controlled
  power, generalized prepared-state reflection/amplification, phase
  syndrome, restricted conditional sequence, explicit parity uncompute.
- All-integer basis truth tables, dirty ancilla counterexample, strict
  complex preparation, controlled relative phase, exact deterministic
  dynamic results, and common-basis gate/depth counts with verified
  strict operator preservation. 32 authored unitary tasks after extension.

## Promotion decision register (preliminary)

| Scope | Initial decision |
|---|---|
| aligned pair angles #142 | Strong candidate for existing pairs= extension; optimize transaction path and approve stub scope |
| layers/scheduling #143–144 | Revise; compare simpler bound row application with existing sweep/loop semantics |
| sequence/tensor/power #145/#149/#158 | Prefer existing apply/repeat/inverse unless distinct held-out benefit |
| commuting evolution #146 | Continue; direct native rotations first, symbolic time and resource contract separate |
| formula #147 | Continue research, explicit order/steps/error; do not silently approximate |
| control #148 | Revise; direct canonical controls and phase checks, avoid general synthesis overhead |
| conjugation #150 | Existing API is competitive; context-manager experiment separate |
| reflection/oracles #151/#153/#154 | Continue scoped recipes; avoid hidden oracle synthesis |
| preparation #152 | Basis/product useful; arbitrary amplitudes have different cost/extension semantics |
| syndromes/arithmetic/feedforward #155–157 | Research recipes with explicit resources and guarantees |
| uncompute #159 | Do not promote automatic cleanup; dirty-input counterexample |
| topology #160 | Compare graph-state recipe to existing pairs= topology; avoid synonyms |

None is approved for public API by this document. A full decision requires
second-run evidence, compatibility and explicit owner scope approval.

## Held-out pilot protocol (#165)

Freeze candidate commit, exact docs and allowed imports, evaluation
rubric, model versions (if agent study) and tasks before evaluation.
Recruit consenting developers separately; randomize matched ordering and
counterbalance experience. Use new instances/families not used to tune
the prototypes; e.g., asymmetric weighted graph, complex preparation
with phase, controlled relative-phase block, and debugging an erroneous
ancilla assumption. No answer leakage or reuse of authored benchmark
snippets as held-out tasks. Equal time, tools, access to documentation
and repair budget; independently score functional correctness and
operator/dynamic contract, invalid assumptions, completion, elapsed time,
token/call count, repair and abstention. Record all failures/exclusions
and separate human vs agent measurements. Report consent, sample size,
uncertainty and limitations. This is a protocol, no participants or model
runs have been completed. Link #112/#113 for independent evaluation.
