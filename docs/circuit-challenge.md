# Ketary Circuit Challenge

Maturity wave #214–#230. The 100 named instances in
research/circuit_challenge.py use Ketary alone to construct candidates;
NumPy/SciPy analytic oracles are separate. These are authored instances,
not 100 distinct algorithms, not independently authored, not hardware
validation. Some vary angles, widths, masks or seed within a family.
Run `python -m pytest -v -rs tests/test_circuit_challenge.py`.
Install pinned optional Aer to execute all 15 measured instances.

| Category | Cases | Oracle |
|---|---:|---|
| Fundamental | 10 | analytic rotations and interference |
| Entanglement | 10 | GHZ and graph amplitudes |
| Algorithms | 15 | DFT, BV, Grover and QPE |
| Parameters | 15 | analytic matrix, zipped independent rows and sequential product |
| Hamiltonians | 15 | dense expm, phase and explicit rejection |
| Oracles | 10 | complete parity and constant truth tables |
| Error syndromes | 10 | ideal bit/phase repetition syndromes |
| Dynamic | 5 | deterministic feedforward/reset, inverse preparation teleportation |
| Composition | 5 | remapping, repeat, inverse, independent compose |
| Verification | 5 | PASS/FAIL/INCONCLUSIVE, reusable contract and evidence |
| Total | 100 | |

A subset of unitary cases checks every basis column and an arbitrary complex
input. Others explicitly check only the algorithm's prepared state or a
measurement/verdict contract. No proof of fault tolerance, hardware noise
or general teleportation channel from these small finite checks.

## Review loop

For every failing case preserve the failing fixture and distinguish API
defect, incorrect oracle, unsupported scope, and infrastructure error.
Do not silently loosen tolerance or skip an inconvenient case. Record
before/after code, strict oracle, complexity, cost and supported mode
before promoting any new abstraction. Reuse existing spellings first.
Pinned external corpus and independently authored held-out cases remain
separate tasks. Shared CI is diagnostic only.
