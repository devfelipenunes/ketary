# Pre-alpha developer pilot protocol

This is a proposed formative usability study, not a completed experiment.
Freeze the exact commit and use the same Python 3.12 environment and dependency
versions. Recruit 3–5 consenting developers with varying quantum experience.
Do not collect credentials, private projects, names or contact details in
public artifacts. Use participant codes and obtain permission for any logs.

## Tasks

Give the problem specification, not the reference implementation. Keep the
same problem and accuracy criteria for both approaches. Provide the respective
official documentation and allow equivalent tooling.

| Task | Expected outcome |
|---|---|
| Bernstein–Vazirani | recover supplied hidden parity mask with correct wire order |
| Phase estimation | decode a known representable phase; document counting register |
| Grover | build or use the bounded marked-state example and verify success probability |
| Simon | recover a secret from orthogonal sampled labels; handle insufficient rank |
| Parameter sweep | estimate Z expectation over four rotation values, preserve binding order |
| Debugging | detect a relative phase divergence, localize observed checkpoint and reproduce witness |

Use research/complete_workflows.py as an authored technical calibration only.
The final task compares the ability to establish an equivalent reproducible
counterexample using available native Qiskit tools or Ketary; record extra
manual work. Do not require the Qiskit participant to use Ketary-specific
artifact schemas. Counterbalance order: approximately half start with Qiskit,
the others with Ketary. Use matched but different input instances on the
second attempt to reduce memorization. Record prior experience and order.

## Measurement

For each task record completion status (correct, incorrect, incomplete),
elapsed active time, attempts, documentation lookups, assistance, observed
mistakes (wire order, mutation, phase, decoding, guarantee scope), source
token count and self-rated clarity (1–5). Set a common 20-minute task cap;
report incomplete/censored tasks separately, not as successful timings.
Record environment, task variant and SDK version. Ask what concepts were
hard to discover and which abstractions helped or obscured understanding.

Report paired task-level results, medians with individual anonymous
observations, and qualitative issues. With 3–5 participants this is formative;
no statistical superiority or population-level conclusion is justified.
Prioritize correctness and clarity over fewer tokens. Do not publish private
participant data. No participant recruitment or data collection is implied
by this document.
