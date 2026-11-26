# ADR 005 — Call-local native Pauli query ownership

Status: candidate pending exact-head qualification. Refs #306 #307 #254.
The integrated #376 diagnostic [job](https://github.com/devfelipenunes/ketary/actions/runs/45830454629/job/139945536432) compared nine bounded canonical-label workloads, with independent scalar oracles. Reused native handle median was lower than fresh native handle in all nine; for 32 labels at 8 wires 0.894624 vs 0.984778 ms. Maximum residual across variants 1.388e-16. Shared-runner data, not a general speedup.

Decision: centralize the native numeric acceptance in _result and reuse a single
Statevector within each grouped real or explicit complex query after existing
full preflight. No cache beyond one invocation, no mutation, no extra state
copy, no new import edge, no alternative math engine. Keep legacy scalar
mapping path and compensated sum order. Test the actual native evaluations,
not an incidental public method dispatch. Exact independent matrix/bit
references, nonfinite faults, near-normalized states, resource preflight,
unique-term order, call-local handle identity and snapshot immutability
must all pass. Preserve previous test intent and acceptance thresholds.

Benchmark the actual candidate against the old grouped path in the same
runner; the narrower #376 research comparison alone cannot justify a runtime
speedup claim. Revert optimization if semantic evidence fails. Dedicated
host and independent evaluation remain outstanding.
