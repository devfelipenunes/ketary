# ADR 003 — Explicit execution, ownership and verification scope

Status: implemented, documented retrospectively.

Context: quantum programs are expensive to evaluate; equal measurement
probabilities do not establish state or operator equivalence.

Decision: mutable circuit builder; independent transforms and defensive
Result snapshots; immutable Observable and Contract; explicit run, sampling,
trace, comparison and evidence reproduction. Preserve native phase and bit
order. Keep statistical and external guarantees distinct. Legacy report
dictionary behavior remains compatible.

Alternatives: implicit lazy reruns; one universal boolean verification
result; automatic backend selection. Rejected due to hidden cost and
ambiguous mathematical guarantees.

Consequences: callers choose a check and its tolerance/resource limits.
Numerical reports are scoped, not formal certificates. Payload limits do not
guarantee RSS; report access is not a simulation.
