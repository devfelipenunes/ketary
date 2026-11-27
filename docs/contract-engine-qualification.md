# Contract engine qualification — independent developer evaluation

Status: protocol and executable examples, not human evidence. Related #165 and #462.
Do not recruit or identify participants through CI. Obtain voluntary consent, use
anonymous IDs, do not collect private source code, and allow withdrawal.

## Tasks and conditions

Use the same final property and guarantee in both conditions: idiomatic Ketary
with a reusable contract versus idiomatic Qiskit/pytest reference. Freeze both
implementations and documentation before recruitment. Counterbalance order and
assign comparable tasks; stratify by Python and quantum programming experience.

| Task | Acceptance oracle |
|---|---|
| Repetition encoder | Logical X/Z transitions and stabilizers, phase mutant detected |
| Reversible compute/action/uncompute | Joint clean workspace and separate coherent action |
| Grover | Target probability on declared input, not full operator equivalence |
| QFT | Strict Fourier reference, distinguish global phase and bit order |
| Debugging | Reproduce a supplied witness and correctly state its scope |
| Budget | Interpret INCONCLUSIVE and UNSUPPORTED without claiming correctness |

Measure independent correctness, scope comprehension, time-to-first-valid
solution, debugging time, help requests and maintenance after a change.
Report individual anonymous outcomes, median and spread, not LOC alone.
Include installation friction and error messages. Do not substitute agent
generated scripts for participants. Formative pilot 3–5 consenting participants,
then define sample size and analysis before confirmatory recruitment. No human
study executed by this change.

Executable corpus: front_proof10.py algorithms/subspace/cross. The current
TransitionContract and RustSession are research-only, not published API.
A public design must remove incidental mask arithmetic while preserving explicit
domain/quantifier, metric, phase and resource scope. Do not change the public
Contract snapshot semantics. Controlled host protocol in release-validation.md
remains required; external reviewer and owner approval remain outstanding.
