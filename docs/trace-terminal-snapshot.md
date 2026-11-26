# Terminal trace snapshot ownership diagnostic

Refs #274 #276 #300 #310. The wire-index experiment showed marginal
gains. This narrow follow-up checks whether terminal-only native output
adoption (existing private Result policy) can eliminate a final copy in
a full trace. All intermediate snapshots remain defensive copies, and
the research cursor is used solely for a complete trace, never arbitrary
repeated terminal requests or further evolution. Pairwise snapshot
non-aliasing and exact per-prefix state equality precede timing.
Six bounded workloads, raw p50/p95, no timing gate. Expected benefit is
small because at most one of count+1 copies is affected. No change to
SDK ownership, public checkpoint behavior, or RSS claim. Do not promote
unless evidence justifies the complexity; no inference of exclusive
ownership from NumPy flags alone.
