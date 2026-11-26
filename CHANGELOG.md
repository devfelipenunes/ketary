# Changelog

## Unreleased (experimental)

- Fluent gate aliases, independent copy, H batches, explicit initial states.
- Bounded inspection, evidence, reusable mathematical contracts and report rendering.
- 29 fixed logical gates plus bounded MCX, native symbolic templates and complete binding.
- Reduced density matrices, purity, Schmidt values, weighted Pauli observables,
  conditional probabilities, pure-state trace distance, Pauli variance and top-k.
- Incremental aligned diagnostics and selected checkpoints and explicit cross-length alignment.
- Bernstein-Vazirani, QFT, small Grover, superdense, phase-gate QPE, Simon iteration and GF(2) recovery.
- Optional native Aer classical shots, reset, bit-conditioned X/Z and teleportation.
- SVG schematics, notebook, documentation, mathematical query benchmarks and CI.

The default bound unitary Circuit and Result behavior is preserved. The dynamic
extra and symbolic mode are explicit opt-ins. No hardware or public release is
approved. See docs/sdk-roadmap.md for limitations and release gates.

- Bounded wire iterables for append/compose, initial-state shape preflight and weighted-observable variance.

- Experimental verification engineering: shared checks, operator metrics, witness search and replay, semantic diff, explicit checkpoints, statistical contracts, query plans, streamed observable variance and isolated external verifier comparison.

- Pre-alpha stabilization: runtime/stub parity tests, consistent purity budget validation, onboarding and verification guides, clean-wheel example and dynamic-extra smoke tests, expanded matched benchmark and artifact metadata checks.
