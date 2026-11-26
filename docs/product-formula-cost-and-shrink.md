# Product-formula cost and generated counterexample reduction

Refs #287 #311. Complements existing 192 strict commutator-bound comparisons
and 1,000 generated mathematical cases, not a new runtime or public API.

## Product formula
54 deterministic workloads: 3 seeds, 3 signed times, 3 step counts, 2
orders. Independent dense ordered products and expm, full native and
common u/cx operator checks including phase, analytical spectral-norm
bound separate from floating point residual. Native and lowered gate
counts, depth, CX count, state payload, construction/lowering/execution
raw p50/p95, counterbalanced randomized order. Same input, no timing
threshold or process RSS/dedicated host claim. Observed convergence is
not guaranteed monotone for arbitrary Hamiltonians.

## Generated failures
Reproduce the existing 250 ordered-unitary seed namespace, independent
dense products and inverse/norm checks. On failure attempt deterministic
single-row deletion with restart, capped at 128 attempts; emit seed and
reduced ordered rows. Fixed initial state and phase, no arbitrary
parameter shrinking or global minimality. Sixteen explicit injected
phase-gate sign faults exercise the failure path and validate a completed
one-deletion local minimum. Other generated families retain seed replay
and manual diagnosis. The new 250 rows are repeats of the existing seed
namespace, not additional distinct generated cases or scientific
applications.
