# Parallel verification and resource qualification

Refs #90 #91 #92 #93 #94 #109 #298. Negative controls cover whole-batch
admission before evolution, bounded iterable consumption, native output
ownership (view, read-only, borrowed, fresh), strict replay validation before
allocation, and planted phase/control/wire changes. Separate selected-only
INCONCLUSIVE from operator verdict; do not equate evidence with root cause.
Profile dense metrics and selected-plus-dense comparison on matched circuits,
3 seeds and 5 repeats. These paths have different payloads and may terminate
on a witness; do not turn their timings into an equal-scope speedup claim.
No precision, public API, cap, or simulator changes. Broader corpus,
dedicated host and optional external-verifier qualification remain open.
