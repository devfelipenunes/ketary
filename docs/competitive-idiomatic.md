# COMP01 — Authored idiomatic pilot

Separate from the common gate-stream microbenchmark. Compare public
Ketary, Qiskit, Cirq and PennyLane APIs for GHZ (2/4/8/12 wires), QFT
(2/4/8, asymmetric basis input), Bernstein–Vazirani (four masks, explicit
ancilla and full coherent output), and a two-wire variational objective
plus its derivative (four angles). Fifteen matched cases; four routes;
three randomized timing seeds, 30 observations per route per case, three
warmups. End-to-end includes device initialization where the authored
solution does it, circuit construction, execution and owned output.
No import timing. No physical gate count comparison for unexpanded
templates. Gradient routes use respective explicit parameter-shift/Jacobian
methods; these are mathematical equivalence tests, not equal internal work.

Independent closed-form oracle: GHZ amplitudes, positive Fourier transform
of |1>, BV mask with minus-state ancilla, E(t)=cos(t)+0.7 sin(t) and its
derivative. Strict absolute error <=1e-9, no phase alignment. Stop on any
mismatch; no timing for invalid case. Record all raw observations and actual
versions. Retain full authored source, lexical tokens (including function
signature but excluding comments/indentation), AST nodes, calls, loops,
LOC. Imports are common setup excluded for all. These are specific authored
solutions, not shortest possible programs, developer productivity, or an
independent held-out study. No change to public API or dependency set.
Remaining algorithm families, noisy/dynamic, compilation, verification and
controlled host are tracked by #507; independent study #165/#462 remains.
