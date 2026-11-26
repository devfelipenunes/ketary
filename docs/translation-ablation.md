# BENCH07 / AUD12: translation ablation

The BENCH04 comparison of prepared QuEST and full lowering includes both
translation and packing, and compares execution on an explicitly lowered
basis. It does not by itself prove that original circuits can bypass
lowering. This experiment directly tests that counterfactual.

## Matched conditions

Same original circuit, exact input (zero and seeded arbitrary complex),
same QuEST library, thread count, result validation/copy, runner and
randomized trial order. Each case compares:

- original Qiskit Statevector (reference);
- forced lowering + Rust packing + QuEST execution;
- pre-lowered circuit + packing + execution;
- pre-lowered and packed execution;
- direct original packing + execution, only if strictly accepted;
- direct pre-packed execution, only if strictly accepted.

Preparation-only experiments separately measure lowering, lowering plus
packing, lowered packing and direct packing. Do not add medians and label
them measured total latency. The direct vs forced comparison reports
paired trial-level ratios and differences. Break-even is an additive
median model, strictly conditional on positive per-run savings, not
observed batch throughput.

The original Rust circuit remains authoritative. Direct packing uses the
existing pinned experimental C ABI, not a name-only whitelist. Unsupported
cases are counted as direct exclusions with reasons; they still participate
in the explicitly lowered benchmark if mathematically valid. No silent
fallback. Published cases are already projected to the stated unitary
scope; excluded dynamic circuits are not successes. Metadata and layout,
classical bits, unbound angles, custom gates and open controls are not
silently discarded.

## Acceptance

Strict complex amplitude, normalization and phase checks against original
Qiskit state; full operator verification of the lowering for width <=8,
selected complex inputs otherwise. All 11 native gate kinds also tested
on every basis input of a small circuit; nine unsupported-input controls,
empty circuit with phase and MCX occupied-spectator oracle. No timing
assertions or tolerance relaxation. Failure to compile or validate is
failure, not an excluded performance row.

36 authored algorithm cases, 60 gate cases and the pinned public corpus
projections, three seeds and 15 randomized repetitions per variant and
input. Retain raw samples, medians/p95, pair order, gates/depth, source
blob, environment, host, commit and exclusions. Results are shared-CI
diagnostics only. Dedicated host, SIMD counters, memory peak, and
cross-hardware conclusions remain separate.
