# Matrix-free variance cancellation and memory audit

Issue #306. Public dense, chunked streamed and minimum-budget fallback
are tested against an independent analytic variance sin(theta)^2 for
H = aI + Z on a rotated product state. 36 cases span identity shifts
up to 2^45 and near eigenstates. Absolute residuals and violations of
1e-9 are recorded rather than silently accepted. Centered H is an
explicit separate oracle/diagnostic; public behavior is unchanged.
18 bounded regression cases at shifts 0 and 2^16 plus negative preflight.

Isolated Linux workers measure own VmHWM before/after one route at a
time, with retained state bytes separate. 60 observations (3 repeats,
4/8/12/16 wires, 4/16 terms, dense only at <=8 wires); all routes compare
to legacy native action, and small cases also to a dense operator.
Raw timings and p50/p95 retained, no timing assertion or dedicated host
claim. Oracle after memory measurement. HWM includes preparation;
increments are not allocation counts. Cancellation deviations at large
shifts are limitations to review, not a certification of accuracy.
