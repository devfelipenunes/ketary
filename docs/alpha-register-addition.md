# Modular register addition — #294

Complements the integrated increment, comparison and composed Boolean
oracle profiles in research/closure_reversible_logic.py. This fourth
distinct intent adds register a into register b modulo 2**n while preserving
a, with no work bits or carry output. Use explicit controlled increments
in existing Ketary primitives; Qiskit ModularAdderGate is the idiomatic
native comparator. Qualify all basis columns, inverse, arbitrary complex
input, reversed mapping and width rejection. Compare common basis u/cx
counts/depth, source tokens and raw build/run measurements over three
seeds and five repeats. Native library source excludes its internal code;
lowering is not part of construction timing. No installed API change,
controlled-host claim or new arithmetic abstraction. Add an atlas pointer
after the preceding atlas candidate is integrated to avoid overlapping
manifest edits. Keep #294 open until the combined evidence is reviewed.
