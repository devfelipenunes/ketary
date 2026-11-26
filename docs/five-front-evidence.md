# Five-front first-cycle evidence

Baseline 7dbbd3fe; merged candidates #265–#269; integrated source at
eb8819646459d377a3e28c2e8aa3148970942272 before this gate.

| PR | Evidence |
|---|---|
| #265 | 22 jobs; 1310 core tests, 27 Aer-only skips, 31 warnings; reject nonfinite imaginary component. |
| #266 | 6 jobs; all 26 runtime modules classified exactly once. |
| #267 | 9 jobs; native direct and preexpanded QAOA references, all objective oracles pass. |
| #268 | 9 jobs; 27 width/gate/seed cases, zero report residual, private snapshot faster in 27/27. |
| #269 | 9 jobs; 18 local-observable workload cases, strict complex states and energy/variance. |

QAOA runner 1101, 5 wires, 3 rows: Ketary/direct/preexpanded/opaque
objective medians 3.211/3.788/4.802/58.381 ms. Native direct construction
0.289 vs Ketary 0.889 ms; direct is faster in one of nine objective
cases. Preexpanded synthesis 3.297 ms separately. Tokens 148/199/206/180.
Same prepared state, energy and variance, not general throughput.

QueryPlan runner 2202, 8 wires/1024 gates: plan 37.134 ms, snapshot
25.749 ms; replay 11.172 ms. Snapshot comparator retains JSON estimate.
All 27 paired cases match exact report schema and zero residual. This
does not implement or authorize a public plan change; memory retention,
replay limits and immutable ownership need separate review.

Observable read/evolve tokens manual 92/101, embedding 48/66, native
50/66. Embedding faster than explicit Ketary in all 18 cases; inputs
shared and excluded, opaque native evolution is not a fair universal
speed comparator. Keep research-only until public contract, stubs and
promotion approval. No new public API in this cycle.

55 candidate jobs across five PRs, each checked on exact head; trees
reconciled with disjoint earlier merged files. Do not sum separate branch
test counts. Combined PR runs the SDK suite and integration fixture; push
CI remains unverified. Independent usability, controlled host/RSS,
external pinned corpus and legal redistribution remain outstanding.
