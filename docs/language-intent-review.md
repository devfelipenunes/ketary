# LANG01–10 language intent review

The SDK uses Python, not a new parser or competing runtime. Qiskit owns
native circuits. The goal is mathematical intent, explicit execution and
reusable verification. This work compares ten authored task families with
ten parameterized cases each, not 100 independent algorithms or participants.

| Front | Current approach | Candidate / decision boundary |
| --- | --- | --- |
| LANG01 | apply_each, named selections | compare ordinary reusable layers; no generic layer object without distinct benefit |
| LANG02 | repeat, times, ordered batches | compare Qiskit repeat, not only hand-written loops |
| LANG03 | explicit X gates | candidate basis(label), X-only unitary, not reset; product/arbitrary preparation separate |
| LANG04 | real Pauli expressions and on | compare from_sparse_list; no arbitrary complex/noncommuting operator product |
| LANG05 | manual occurrence shift | candidate expectation_jacobian, shared-parameter chain rule, no arbitrary generator or optimizer |
| LANG06 | symbolic exact commuting evolve | strict global phase; no implicit approximation |
| LANG07 | controlled gate primitives | compare native controlled composite with relative phase; general synthesis remains research |
| LANG08 | Contract and explicit verification | positive and negative sentinel, no formal proof claim |
| LANG09 | shared identity and ordered placements | authored held-out style examples, no independent LLM study |
| LANG10 | bounded sweeps and four core concepts | lexical vocabulary/AST metrics; no unnecessary aliases |

Run python -m research.language_corpus --output language-corpus.json.
Compare current, candidate, and idiomatic Qiskit sources with shared
inputs. Validate full operators (not just probabilities), numerical output,
analytic shared derivative and positive/negative verdict. Raw timings
include the different authored workloads, not an isolated native benchmark.
Keep losing cases. Human evaluation and dedicated host remain separate.
The new APIs are advanced, additive, and have explicit caps and tests.
