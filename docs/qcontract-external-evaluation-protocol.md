# B7 external usability and reproducibility protocol (not yet executed)

## Research questions
1. Can a developer state the intended property correctly without learning
   packed masks or verifier internals?
2. Does the contract find a real error with less debugging effort than
   a conventional Qiskit/pytest workflow?
3. Which syntax makes domain and assumptions easiest to understand?
4. Do users distinguish INCONCLUSIVE/UNSUPPORTED from a refutation?

## Participants and ethical boundary
Recruit 5–10 volunteer developers with Qiskit familiarity, at least
two reviewers familiar with quantum formal methods. Obtain informed
consent, disclose experimental nature, avoid collecting credentials or
unnecessary personal data. No study results or recruitment claimed.
Use anonymized IDs and optional experience bands. Participants may
withdraw. No private code in published artifacts without permission.

## Counterbalanced task design
Supply a frozen A4 baseline, candidate syntax, identical examples,
one supported Python environment and reference documentation.
Alternate baseline/candidate order across participants and use equivalent
task variants to mitigate learning/order bias. Timebox each task
(e.g. 15 min), report incomplete tasks rather than discard them.
Observe without leading participants; offer same predefined hints.
Record self-reported prior exposure, not infer from performance.

| Task | Baseline | QContract variant | Success criterion |
|---|---|---|---|
| Bell phase mutation | Qiskit expectation test | named zero-input stabilizers | detect X correlation violation, preserve Z correlation |
| Conjugation vs state | custom matrix test | all-input invariant vs zero-input | distinguish quantification correctly |
| Ancilla leak | reference circuit / dense test | clean-input contract | identify omitted uncompute |
| Equivalent rewrites | Operator/QCEC | phase-explicit equivalence | distinguish equivalent and mutant |
| CI gate | pytest | plan.require() | reject unresolved outcomes |
| Limits | budget/time cap | inconclusive result | do not falsely claim FAIL or PASS |

Metrics: completion rate, elapsed time, number of attempts, wrong
quantifier choice, false accept/reject, assistance count, diagnosis
quality, perceived ease (1–5) and free-text feedback. No significance
claim from small convenience samples. Publish anonymized raw outcomes
and limitations, not just means. Independent reviewers evaluate the
semantic specification, witnesses, replay assumptions and benchmark
fairness separately.

## B6 controlled performance
Freeze exact source SHA, dependency lock, hardware model, OS, clock,
affinity and thread settings. Record idle/load conditions, run fresh
processes, warmup and randomized interleaving where possible, compare
same outputs with equal input preparation. Retain raw timings and
peak process RSS; separate allocation, native work and logical budget.
Use fixed corpus plus held-out seeds and repeated hosts; record timeouts,
resource exhaustion, unsupported and inconclusive cases. A paired
same-host median ratio and sample-bootstrap analysis are exploratory
until independent repeatability. Do not compare wall time across
different hardware as if same experiment. Publish losses.

## Release gate
A local Alpha may proceed with external study listed as pending only if
mathematics, correctness, installability, scope and essential usability
tests are validated. No external adoption or superiority claim. Research
publication requires external review/replication and a prior-art analysis.
