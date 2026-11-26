# ADR 005 — Bound append staging and dependency guards

Status: candidate, requires exact-head CI and review.

Use validated small blocks and native in-place composition for bound
batch/apply, with suffix/phase rollback on ordinary native exceptions.
Self-application copies the source. Keep symbolic/classical batch and
compute-action-uncompute on the existing conservative paths until their
semantics are independently validated. No concurrency guarantee.
Pure residual computation belongs beside snapshot checks, Pauli label
validation in the foundation; remove two reverse import edges without
moving public classes or changing schemas. Test all explicit import
boundaries and baseline cyclic membership. No assertion of complete
runtime acyclicity. Benchmark matched operations before claiming gains.
