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

Follow-up: the original 36-case audit found 16 route violations at shifts
2^30 and 2^45 (max 1.9379016801659987e-4). The minimum-budget route
is not always the native fallback: at one wire it is, at larger widths
it may use short chunks. The follow-up includes one-wire fixtures and
labels this route accurately. The runtime now validates all coefficients
then removes the exact identity offset prior to both variance paths.
Strict 1e-12 analytic tests cover shifts through max finite double,
negative shifts, identity-only, preflight and noncommuting sums.
