# QPE specialized construction qualification — candidate

Refs #180 #52 #56. Known phase only: the existing factory prepares the
target eigenstate, emits modulo-reduced controlled phase gates and composes
an independent inverse QFT. Compare that factory with a direct append
sequence (reverse swaps, ascending target/control order, negative CP,
H last). Both Ketary paths include export; generic native powers and manual
CP use QFTGate and are distinct representations until common-basis lowering.
Do not change the public factory before paired results. Preserve zero-angle
instructions, exact logical order, phase, wire mapping and cap of 12 bits.
Require native circuit equality up to precision 12, complete strict operator
equality at small widths and independent exact-grid/off-grid distributions.
Archive 3 precisions × 3 phases × 3 seeds × 9 repeats, common gates/CX/depth.
No generic QPE, hardware, or cross-host speed claim. Keep #180 open until
reviewed full artifact and integrated decision.

## Runtime promotion candidate

The qualified research head showed faster direct construction with identical
logical circuits and strict operators. The installed factory now proposes
the direct sequence, preserving the historical composed implementation as
an independent benchmark and structure reference. Validate actual installed
factory output against the historical route, including precision 12 and
near-one phase. No new API. Final integration remains subject to exact-head
CI and raw profile review; the dedicated-host gate is unchanged.
