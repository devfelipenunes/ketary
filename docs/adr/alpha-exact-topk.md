# Candidate ADR — Exact scalar scoring with bounded chunk selection

Refs #310 #303 #92. Prior integrated research #479 demonstrated scalar-score
chunk selection at k=32, but vectorized complex magnitude reordered near ties.
Restrict candidate to snapshots >=1024 elements and 8<=k<=32. Use precisely
the original scalar score, lexicographic descending score/ascending index,
and original scalar probability formatting. Other k values retain the heap.
Temporary arrays scale with 1024+k rather than snapshot width; this is not
a claim of lower peak memory than the original heap, which already uses O(k)
space. No public signature, dtype, tolerance, snapshot ownership or cap changes.

Benchmark the complete public output for 3 widths, 5 k values, 3 seeds and
5 repeats, including fallback routes. Separate Linux processes at 18/20q
record pre-operation and post-operation VmHWM and output digests. Fixture
construction is chunked to limit avoidable setup temporaries; lifetime HWM
may still mask allocations. Require exact ordered dictionary equality and
adversarial near-tie fixtures. Do not integrate if measured regressions or
unacceptable scratch cost outweigh the benefit. Shared CI not dedicated host.
