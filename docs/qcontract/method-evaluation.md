# Contract-first methodology — evaluation addendum (candidate)

Complement #165/#462 and the existing formative study packet
(docs/alpha-study-packet.md), not a replacement or approval of that
protocol. No recruitment, participant observations or reviewer approval.
The older tasks include parameterized rotations and Hamiltonian workflows
outside the exact Alpha gate domain. Do not interpret performance on
those tasks as evidence of exact contract verification.

## Hypotheses and matched conditions

H1: designing an explicit scope and obligation before implementation
improves requirement correctness and defect diagnosis.
H2: named contracts and explicit wire masks reduce API friction.
H3: equivalent/allowed variations are accepted without weakening true
requirements.

To separate workflow from tooling, propose three matched conditions:
A: Qiskit with ordinary tests and its own official documentation;
B: QContract API with neutral API reference and ordinary test-first or
implementation-first workflow selected by participant;
C: same QContract API with contract-design canvas and contract-first method.
Use same admitted gate set, independent task rubric, reference oracle,
time cap, hardware, exact dependency versions and assistance policy.
Randomize/counterbalance task variants and order before observing results.
A vs B primarily probes tool availability; B vs C probes method guidance.
These are formative contrasts, not causal claims from a tiny pilot.
Independent reviewer must approve task matching and order before recruitment.

## Reviewer-only scoring dimensions

Score the intended scope, correct positive behavior, detection of
a seeded genuine defect, acceptance of allowed variation, and correct
handling of unresolved/unsupported results separately. Do not score
a passing contract as complete correctness. Retain actual source and
outputs, time to first independently correct result, repair attempts,
documentation lookups, invalid input errors and assistance. Measure
tokens only in an agent study with fixed model/configuration. Record
timeouts and failures; do not discard them. Separate author-created
smoke cases from reviewer-selected held-out tasks. Do not give the
solutions or oracle fixtures to participants.

Proposed task families for independent reviewer selection: prepare a
small stabilizer target, preserve logical action while cleaning a
workspace, diagnose a phase-sensitive rewrite. Keep all circuits in
the admitted Clifford+T alphabet; phase policy and input scope must
be declared. Avoid reuse of the already published teaching examples
as secret held-out tasks. A reviewer must create/approve unseen variants.

## Prior work and differentiation

- Quantum Correctness by Construction, OOPSLA 2025:
  https://doi.org/10.1145/3720433
- QBricks deductive verification:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7984546/
- Quantum Testing in the Wild, Qiskit Algorithms:
  https://ieeexplore.ieee.org/abstract/document/10992535
- QuCheck property-based testing:
  https://arxiv.org/abs/2503.22641
- QMutPy mutation testing:
  https://doi.org/10.1145/3533767.3543296

These are relevant predecessors, not evidence of novelty or of superiority.
QContract's proposed practical distinction is an installed, exact,
bounded contract layer and a specification-design workflow that leaves
Qiskit as the source circuit representation. Test whether that distinction
actually helps developers; do not assume that it does.

External study remains open under #165/#462. No public release,
no new mathematical domains and no expansion of hardware support.
