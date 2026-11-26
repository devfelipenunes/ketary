# Abstraction opportunity laboratory — issues #141–#166

This is a research-only follow-up to #106. The older ABS01–ABS36 design
inventory uses historical labels; the issue numbers #141–#166 identify
this new wave unambiguously. No installed API, alternate circuit IR,
new dependency or release. Only ordinary native-backed Circuit outputs.

## First experimental slice

| Issue | Candidate or experiment | Remaining work |
|---|---|---|
| #141 | 27 authored matched unitary tasks and two dynamic patterns | Pin external circuit instances and add held-out corpus |
| #142 | aligned pair angles | Evaluate candidate overhead; public overload RFC |
| #143–144 | template rows and sequential composition | Distinguish scheduling from independent sweeps; no runtime scheduler |
| #145 | ordered block sequence | Decide whether current apply is enough |
| #146 | commuting Pauli evolution, exact global phase | Efficient lowering and symbolic time |
| #147 | explicit first/second order product formulas | Error scaling, wider corpus |
| #148–149 | bounded closed controlled blocks, signed integer powers | Coverage, expansion, relative phase and efficient lowering |
| #150 | explicit conjugation factory | Compare context manager and existing API; no automatic cleanup |
| #151 | reflection about prepared state | More general amplification and promise checks |
| #152 | basis preparation | Product/amplitude preparation study still outstanding |
| #153–154 | parity and Pauli rotations, existing oracles as baseline | Composite Boolean oracles and arbitrary inputs |
| #155 | repetition-code syndrome with injected X errors | Phase-error code and stabilizer scope |
| #156 | modulo increment, complete truth table | Adders, comparison and modular arithmetic |
| #157 | existing single-bit feedforward recipe | Generalized conditions not implemented |
| #158 | tensor, power, sequence | No operator-overload DSL |
| #159 | explicit reversible conjugation | Automatic uncomputation remains feasibility research |
| #160 | graph-state recipe | Compare existing topology composition |
| #161–162 | matched lexical/AST, strict operators, complex states, raw times, analytic oracles | Actual artifacts and validation; no noisy timing gates |
| #163–164 | cross-family cases and existing canonical API baseline | Decision on redundant names, docs, stubs |
| #165 | external developer/agent protocol | Actual independent experiments not done |
| #166 | decision criteria below | Promotion after evidence and review |

## Evaluation

Authored snippets are static local fixtures, not external or user-provided
code. Shared inputs/imports are not counted; include candidate helper
implementation separately in maintenance assessment. Count lexical tokens,
AST nodes, loops, calls, numeric literals. Compare existing Ketary,
experimental Ketary and idiomatic native Qiskit, including QFTGate and
PauliEvolutionGate where appropriate. Logical instruction counts are **not**
expanded gate counts for opaque native gates; do not compare as if they
were physical cost. Strict full matrices and arbitrary complex initial
states are required for every unitary task. Timings include construction
or statevector with copied output, separately; no universal performance
claim from shared CI. Three seeds/runners, seven randomized repetitions.
Dynamic recipes use deterministic Aer counts, not a statevector oracle.

Independent dense NumPy Pauli matrices and scipy expm are oracles, not
another simulator shipped in the SDK. Bounds: <=8 wires, <=4096 staged
operations, <=32 parameter rows, <=256 placements, controls total <=5
wires and <=16 source gates, first/second order formulas <=32 steps.
Construction is explicit and never runs a statevector; source Circuits
are not mutated. Controlled synthesis is restricted research use and
requires a strict full operator oracle. No hidden ancillas or approximate
fallback. Product formula time error is measured, never advertised exact.

References for task families (authored instances, not copies of benchmark
files): MQT Bench https://mqt.readthedocs.io/projects/bench/en/stable/ ;
QASMBench https://doi.org/10.1145/3550488 ; Qiskit Circuit Library
https://quantum.cloud.ibm.com/docs/en/qiskit/circuit-library ;
Q# conjugation https://learn.microsoft.com/en-us/azure/quantum/user-guide/language/expressions/conjugations ;
Cirq circuit operations https://quantumai.google/cirq/build/circuits .

## Promotion rules

Keep every negative outcome. Existing 254 vs 404 token result remains
historical evidence. A candidate is accepted only after it demonstrates
cross-family reuse or a concrete task gap, semantic/ownership/resource
correctness, no unjustified runtime overhead, and a smaller or clearer
canonical vocabulary. A candidate with more tokens can still be useful
if mathematical intent is clearer, but this needs separate user evidence.
No independent usage, agent evaluation or dedicated hardware claim from
this suite. #165 requires actual consenting developers or controlled
model evaluations; #166 requires explicit API scope approval and complete
stubs/inventory/compatibility review. A prototype is not a completed issue.
