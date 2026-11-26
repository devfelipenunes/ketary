# Constrained QAOA applications — qualification candidate

Refs #291 #255 #242 #352. Three distinct synthetic optimization objectives:
weighted independent set, weighted vertex cover, cardinality-constrained
portfolio selection with an explicit toy pair-risk cost. No financial advice
or empirical finance/quantum advantage claim.

Four bits, all sixteen assignments enumerated; penalty adequacy checked on
these exact instances. A finite Walsh transform supplies the diagonal Pauli
Hamiltonian (identity phase retained). Native Qiskit uses explicit RZ/RZZ and
RX gates; Ketary uses Observable and evolve. An independent dense phase
vector and tensor-product mixer validate the full complex state at every
point of a fixed 25-point grid per objective. Report exact classical minimum,
best grid expectation, probability of a feasible or optimal sample, maximum
state residual and raw paired construction/execution samples. Alternating
route order is diagnostic, not a dedicated-host performance comparison.
No continuous optimum or global convergence claim.

Run: python -m research.constrained_qaoa --output constrained-qaoa.json
Tests: python -m pytest -q tests/test_constrained_qaoa.py

## Corpus accounting

The earlier 37-task capability matrix and its alternate recovery routes
measure SDK feature coverage; they are not automatically application intents.
Batch 1 has 12 scientific fixtures (exclude native annotation/barrier checks).
Batch 2 has 27 scientific fixtures (exclude atomic synthesis fault check;
parameterized Hubbard variants count once). This batch adds three objective
fixtures, giving 42 candidate fixture rows across these three batches.
Do not call these 42 globally distinct or claim they all satisfy APP acceptance:
some overlap the wider repository corpus (e.g. parity recovery, Fourier phase
estimation, graph/stabilizer and variational families). The 100-intent target
requires semantic review of all earlier application and held-out corpora,
matched native reference programs, independent oracle and reproducible runs.
