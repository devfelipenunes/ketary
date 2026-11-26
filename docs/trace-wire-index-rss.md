# Trace wire-index attribution and process RSS

Refs #256 #310 #300 #274 #276 #305. Research-only cursor precomputes a
call-local native qubit-to-index mapping; it uses identical Statevector
evolution and defensive Result construction. Six 4/8-qubit trace workloads
(32/128/256 gates), full per-prefix complex state oracle and randomized
paired median/p95 with three warmups. Four tests include repeated indices,
multiple-register native input, snapshot isolation, early divergence,
and preflight. No snapshot adoption or public behavior change.

Separate Linux processes record /proc VmRSS and VmHWM before/after bounded
256-step trace and 10k-prefix compute/action/uncompute. Three replicates
per route, alternating order; results are high-water process images, not
allocator delta or dedicated-host guarantee. Trace payload shown separately.
Composition compares current against the #380 research route; no new
runtime optimization. Preserve raw measurements even if candidate regresses.
