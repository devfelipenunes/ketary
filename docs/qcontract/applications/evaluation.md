# Application portfolio evaluation and integration

Baseline: main 6f236f089e14138f7f2f373d7692dddfa679a21a.
PR #549 (finite-error audit) and #550 (ten applications) were individually
qualified on three installed-wheel platforms and six SDK jobs, then merged.
PR #551 (fourteen algorithms, 103 cases) also passed all nine jobs at
7c1dbe8bbf79be0938d89100ebc249a9d373cb79, but merge returned HTTP 405
because both branches inserted workflow steps at the same location.
This integration candidate copies the five #551 application files unchanged
onto current main and preserves both earlier workflow steps. It requires
new exact-head qualification; do not infer combined success.

## Engineering evaluation

| Front | Delivered or outstanding |
|---|---|
| Expressivity | 25 applications, all ten admitted families, 157 primary scenarios; explicit boundaries on general rotations, hardware and dynamic execution |
| Ergonomics | Existing API only; compare actual requirements before proposing changes; no human productivity measurements |
| Scaling | 4/8/16/32/64-wire GHZ resources, each with correct, phase-error and missing-link controls; one obligation per wire |
| Diagnosis | Two independent H generator obligations vs a single obligation; predeclared three defects and one allowed rewrite |
| Performance | Record raw preparation and verification durations separately in shared CI; no controlled speedup claim |
| Qiskit comparison | Existing small independent numeric oracles; analytic large GHZ predictions avoid dense allocation |
| Agents | Existing frozen-intent gate examples; real agents and held-out tasks still need independent evaluation |

The scaling workload adds 15 cases and 372 per-case obligation comparisons
(3 times the sum of the five widths). Every case also checks status-only
parity and the zero-quota unresolved control. A separate diagnostic
workload has five cases. Expected single-claim defect detection 2/3;
full plan 3/3; allowed rewrite accepted by both. These are expectations
until the new CI succeeds, not observed measurements. The diagnostic
example is a reproducibility check, not a new independent application.

## Acceptance

Run all three existing application suites, the evaluation script, and
the prior method qualification in one installed-wheel job per platform.
Retain separate JSON artifacts; require the six general SDK jobs too.
The existing method audit counts method rounds separately from applications.
Do not inflate the application count with scale variants or duplicate
diagnostic fixtures. CI wall time is exploratory, not a dedicated-host
benchmark (#100). Real developer/agent experiments (#165/#462) and release
approval (#35) remain outside these authored tests.
